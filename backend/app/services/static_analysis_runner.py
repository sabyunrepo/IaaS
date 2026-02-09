"""
backend/app/services/static_analysis_runner.py
정적 분석 도구 실행 관리자

shallow clone → Lizard/Semgrep/Radon 실행 → 결과 수집 → 정리

후보자가 수정한 파일만 분석하여 정확도를 보장.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from app.models.static_analysis import (
    FileMetric,
    FunctionMetric,
    SecurityFinding,
    StaticAnalysisResult,
)

logger = logging.getLogger(__name__)

# Clone timeout (seconds)
CLONE_TIMEOUT = 60
# Analysis timeout per tool (seconds)
TOOL_TIMEOUT = 120


class StaticAnalysisRunner:
    """정적 분석 도구 실행 관리자

    shallow clone → 도구 실행 → 결과 수집 → 정리
    """

    async def run_analysis(
        self,
        repo_url: str,
        target_files: list[str] | None = None,
        token: str | None = None,
    ) -> StaticAnalysisResult:
        """후보자 파일 대상 정적 분석 파이프라인

        Args:
            repo_url: GitHub repository URL
            target_files: PyDriller가 식별한 후보자 수정 파일 경로 목록.
                          지정 시 해당 파일만 분석 (남의 코드 분석 방지).
                          미지정 시 전체 레포 분석 (fallback).
            token: GitHub OAuth token for private repos

        Returns:
            StaticAnalysisResult
        """
        clone_dir = await self._shallow_clone(repo_url, token)
        try:
            results = await asyncio.gather(
                self._run_lizard(clone_dir, target_files),
                self._run_semgrep(clone_dir, target_files),
                self._run_radon(clone_dir, target_files),
                return_exceptions=True,
            )

            lizard_result = results[0] if not isinstance(results[0], Exception) else {}
            semgrep_result = results[1] if not isinstance(results[1], Exception) else {}
            radon_result = results[2] if not isinstance(results[2], Exception) else {}

            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    tool_name = ["lizard", "semgrep", "radon"][i]
                    logger.warning(f"Static analysis tool {tool_name} failed: {r}")

            return self._aggregate(clone_dir, lizard_result, semgrep_result, radon_result, target_files)
        finally:
            shutil.rmtree(clone_dir, ignore_errors=True)

    async def _shallow_clone(self, repo_url: str, token: str | None) -> str:
        """git clone --depth=1 → temp dir"""
        clone_dir = tempfile.mkdtemp(prefix="static_analysis_")

        # Build clone URL with token for private repos
        clone_url = repo_url
        if token and "github.com" in repo_url:
            # https://github.com/owner/repo → https://x-access-token:TOKEN@github.com/owner/repo.git
            parts = repo_url.replace("https://github.com/", "").rstrip("/")
            clone_url = f"https://x-access-token:{token}@github.com/{parts}.git"
        elif not clone_url.endswith(".git"):
            clone_url = clone_url.rstrip("/") + ".git"

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "git", "clone", "--depth=1", "--single-branch",
                    clone_url, clone_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=CLONE_TIMEOUT,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"git clone failed: {stderr.decode()[:500]}")
        except asyncio.TimeoutError:
            shutil.rmtree(clone_dir, ignore_errors=True)
            raise RuntimeError(f"git clone timed out after {CLONE_TIMEOUT}s")

        return clone_dir

    async def _run_lizard(
        self, clone_dir: str, target_files: list[str] | None = None,
    ) -> dict:
        """Lizard: 17개 언어 CC + NLOC (per-function)"""
        cmd = ["lizard", "--xml"]
        if target_files:
            # Lizard accepts file paths as arguments
            existing = [
                os.path.join(clone_dir, f) for f in target_files
                if os.path.exists(os.path.join(clone_dir, f))
            ]
            if not existing:
                return {}
            cmd.extend(existing)
        else:
            cmd.append(clone_dir)

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=TOOL_TIMEOUT,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0 and not stdout:
                logger.warning(f"Lizard returned non-zero: {stderr.decode()[:200]}")
                return {}
            return self._parse_lizard_xml(stdout.decode(), clone_dir)
        except (asyncio.TimeoutError, FileNotFoundError) as e:
            logger.warning(f"Lizard execution failed: {e}")
            return {}

    def _parse_lizard_xml(self, xml_str: str, clone_dir: str) -> dict:
        """Parse Lizard XML output → structured metrics"""
        if not xml_str.strip():
            return {}

        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError:
            logger.warning("Failed to parse Lizard XML output")
            return {}

        function_metrics: list[dict] = []
        file_metrics: list[dict] = []
        language_nloc: dict[str, int] = {}
        total_nloc = 0
        all_cc: list[int] = []
        max_cc = 0

        for item in root.iter("item"):
            # Each item is a function
            name_el = item.find("name")
            if name_el is None:
                continue

            func_name = name_el.text or ""
            file_el = item.find("file")
            file_path = (file_el.text or "") if file_el else ""
            # Make path relative to clone_dir
            if file_path.startswith(clone_dir):
                file_path = file_path[len(clone_dir):].lstrip("/")

            cc_el = item.find("cyclomatic_complexity")
            cc = int(cc_el.text) if cc_el is not None and cc_el.text else 0
            nloc_el = item.find("nloc")
            nloc = int(nloc_el.text) if nloc_el is not None and nloc_el.text else 0
            token_el = item.find("token_count")
            tokens = int(token_el.text) if token_el is not None and token_el.text else None

            # Detect language from extension
            ext = Path(file_path).suffix.lower()
            lang = _ext_to_language(ext)

            function_metrics.append({
                "function_name": func_name,
                "file_path": file_path,
                "language": lang,
                "cyclomatic_complexity": cc,
                "nloc": nloc,
                "token_count": tokens,
            })

            all_cc.append(cc)
            if cc > max_cc:
                max_cc = cc
            total_nloc += nloc
            language_nloc[lang] = language_nloc.get(lang, 0) + nloc

        # Sort by CC descending, keep top 20
        function_metrics.sort(key=lambda f: f["cyclomatic_complexity"], reverse=True)

        return {
            "function_metrics": function_metrics[:20],
            "language_breakdown": language_nloc,
            "total_nloc": total_nloc,
            "overall_avg_cc": sum(all_cc) / len(all_cc) if all_cc else 0.0,
            "overall_max_cc": max_cc,
        }

    async def _run_semgrep(
        self, clone_dir: str, target_files: list[str] | None = None,
    ) -> dict:
        """Semgrep: 보안/패턴 분석 (SARIF output)"""
        cmd = [
            "semgrep", "scan",
            "--config=auto",
            "--sarif",
            "--quiet",
            "--max-target-bytes=1000000",
            "--timeout=30",
        ]

        if target_files:
            for f in target_files:
                full_path = os.path.join(clone_dir, f)
                if os.path.exists(full_path):
                    cmd.extend(["--include", f])

        cmd.append(clone_dir)

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=TOOL_TIMEOUT,
            )
            stdout, stderr = await proc.communicate()
            # Semgrep returns non-zero when findings exist
            if not stdout:
                return {}
            return self._parse_semgrep_sarif(stdout.decode(), clone_dir)
        except (asyncio.TimeoutError, FileNotFoundError) as e:
            logger.warning(f"Semgrep execution failed: {e}")
            return {}

    def _parse_semgrep_sarif(self, sarif_str: str, clone_dir: str) -> dict:
        """Parse Semgrep SARIF output → security findings"""
        if not sarif_str.strip():
            return {}

        try:
            sarif = json.loads(sarif_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Semgrep SARIF output")
            return {}

        findings: list[dict] = []
        severity_counts = {"error": 0, "warning": 0, "note": 0}

        for run in sarif.get("runs", []):
            for result in run.get("results", []):
                rule_id = result.get("ruleId", "unknown")
                level = result.get("level", "warning")
                message = result.get("message", {}).get("text", "")

                locations = result.get("locations", [])
                file_path = ""
                line = 0
                if locations:
                    phys = locations[0].get("physicalLocation", {})
                    uri = phys.get("artifactLocation", {}).get("uri", "")
                    file_path = uri
                    line = phys.get("region", {}).get("startLine", 0)

                severity_counts[level] = severity_counts.get(level, 0) + 1
                findings.append({
                    "rule_id": rule_id,
                    "severity": level.upper(),
                    "message": message[:300],
                    "file_path": file_path,
                    "line": line,
                    "tool": "semgrep",
                })

        # Security score: start at 100, deduct by severity
        score = 100
        score -= severity_counts.get("error", 0) * 15
        score -= severity_counts.get("warning", 0) * 5
        score -= severity_counts.get("note", 0) * 1
        score = max(0, min(100, score))

        return {
            "security_findings": findings[:20],  # Top 20
            "security_score": score,
        }

    async def _run_radon(
        self, clone_dir: str, target_files: list[str] | None = None,
    ) -> dict:
        """Radon: Python MI/Halstead (Python 전용)"""
        # Filter to Python files only
        py_targets: list[str] = []
        if target_files:
            py_targets = [
                os.path.join(clone_dir, f) for f in target_files
                if f.endswith(".py") and os.path.exists(os.path.join(clone_dir, f))
            ]
        else:
            # Find all .py files in clone_dir
            for root, _dirs, files in os.walk(clone_dir):
                for fname in files:
                    if fname.endswith(".py"):
                        py_targets.append(os.path.join(root, fname))

        if not py_targets:
            return {}

        # Run radon mi (maintainability index) with JSON output
        cmd = ["radon", "mi", "-s", "-j"] + py_targets

        try:
            proc = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=TOOL_TIMEOUT,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0 and not stdout:
                return {}
            return self._parse_radon_json(stdout.decode(), clone_dir)
        except (asyncio.TimeoutError, FileNotFoundError) as e:
            logger.warning(f"Radon execution failed: {e}")
            return {}

    def _parse_radon_json(self, json_str: str, clone_dir: str) -> dict:
        """Parse Radon MI JSON output"""
        if not json_str.strip():
            return {}

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse Radon JSON output")
            return {}

        mi_values: list[float] = []
        for file_path, mi_info in data.items():
            if isinstance(mi_info, dict):
                mi_val = mi_info.get("mi")
            elif isinstance(mi_info, (int, float)):
                mi_val = float(mi_info)
            else:
                continue
            if mi_val is not None:
                mi_values.append(float(mi_val))

        if not mi_values:
            return {}

        avg_mi = sum(mi_values) / len(mi_values)
        return {
            "maintainability_index": round(avg_mi, 2),
        }

    def _aggregate(
        self,
        clone_dir: str,
        lizard_result: dict,
        semgrep_result: dict,
        radon_result: dict,
        target_files: list[str] | None = None,
    ) -> StaticAnalysisResult:
        """모든 도구 결과를 통합"""
        # Lizard data
        function_metrics = [
            FunctionMetric(**fm)
            for fm in lizard_result.get("function_metrics", [])
        ]

        # Build file metrics from function metrics
        file_data: dict[str, dict] = {}
        for fm in lizard_result.get("function_metrics", []):
            fp = fm["file_path"]
            if fp not in file_data:
                file_data[fp] = {
                    "file_path": fp,
                    "language": fm["language"],
                    "total_nloc": 0,
                    "cc_values": [],
                    "function_count": 0,
                }
            file_data[fp]["total_nloc"] += fm["nloc"]
            file_data[fp]["cc_values"].append(fm["cyclomatic_complexity"])
            file_data[fp]["function_count"] += 1

        file_metrics = []
        for fp, fd in file_data.items():
            cc_vals = fd["cc_values"]
            file_metrics.append(FileMetric(
                file_path=fd["file_path"],
                language=fd["language"],
                total_nloc=fd["total_nloc"],
                avg_cc=sum(cc_vals) / len(cc_vals) if cc_vals else 0.0,
                max_cc=max(cc_vals) if cc_vals else 0,
                function_count=fd["function_count"],
            ))

        # Semgrep data
        security_findings = [
            SecurityFinding(**sf)
            for sf in semgrep_result.get("security_findings", [])
        ]

        # Documentation ratio: count Python files with docstrings
        doc_ratio = self._calculate_doc_ratio(clone_dir, target_files)

        # Test detection
        test_count, total_files = self._detect_tests(clone_dir, target_files)

        return StaticAnalysisResult(
            language_breakdown=lizard_result.get("language_breakdown", {}),
            file_metrics=file_metrics,
            function_metrics=function_metrics,
            overall_avg_cc=lizard_result.get("overall_avg_cc", 0.0),
            overall_max_cc=lizard_result.get("overall_max_cc", 0),
            total_nloc=lizard_result.get("total_nloc", 0),
            security_findings=security_findings,
            security_score=semgrep_result.get("security_score", 100),
            maintainability_index=radon_result.get("maintainability_index"),
            halstead_volume=radon_result.get("halstead_volume"),
            documentation_ratio=doc_ratio,
            has_tests=test_count > 0,
            test_file_count=test_count,
            test_to_code_ratio=test_count / max(total_files, 1),
        )

    def _calculate_doc_ratio(
        self, clone_dir: str, target_files: list[str] | None = None,
    ) -> float:
        """Python 파일의 docstring 보유 비율 계산"""
        py_files = []
        if target_files:
            py_files = [
                os.path.join(clone_dir, f) for f in target_files
                if f.endswith(".py") and os.path.exists(os.path.join(clone_dir, f))
            ]
        else:
            for root, _dirs, files in os.walk(clone_dir):
                for fname in files:
                    if fname.endswith(".py"):
                        py_files.append(os.path.join(root, fname))

        if not py_files:
            return 0.0

        import ast

        files_with_docs = 0
        parseable_files = 0
        for fp in py_files[:100]:  # Limit for performance
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                    source = fh.read()
                tree = ast.parse(source)
                parseable_files += 1

                has_doc = False
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if (node.body and isinstance(node.body[0], ast.Expr)
                                and isinstance(node.body[0].value, ast.Constant)
                                and isinstance(node.body[0].value.value, str)):
                            has_doc = True
                            break
                if has_doc:
                    files_with_docs += 1
            except (SyntaxError, OSError):
                continue

        return files_with_docs / max(parseable_files, 1)

    def _detect_tests(
        self, clone_dir: str, target_files: list[str] | None = None,
    ) -> tuple[int, int]:
        """테스트 파일 감지 (test_*.py, *_test.py, *.spec.ts 등)"""
        test_patterns = ("test_", "_test.", ".spec.", ".test.", "tests/", "__tests__/")
        test_count = 0
        total_count = 0

        if target_files:
            for f in target_files:
                total_count += 1
                f_lower = f.lower()
                if any(p in f_lower for p in test_patterns):
                    test_count += 1
        else:
            for root, _dirs, files in os.walk(clone_dir):
                # Skip .git
                if ".git" in root:
                    continue
                for fname in files:
                    ext = Path(fname).suffix.lower()
                    if ext in (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs"):
                        total_count += 1
                        rel_path = os.path.join(root, fname).lower()
                        if any(p in rel_path for p in test_patterns):
                            test_count += 1

        return test_count, total_count


def _ext_to_language(ext: str) -> str:
    """파일 확장자 → 언어 이름"""
    mapping = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".c": "C",
        ".h": "C",
        ".cpp": "C++",
        ".hpp": "C++",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".cs": "C#",
        ".lua": "Lua",
    }
    return mapping.get(ext, "Unknown")
