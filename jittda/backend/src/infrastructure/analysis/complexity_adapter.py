"""
Radon/Lizard Adapter — 코드 복잡도 메트릭 산출.

Python 코드: Radon (CC, Halstead, MI) + Lizard (CC 보조)
다국어 코드: Lizard (CC 산출 — JS, Java, Go 등)
"""
from domain.analysis.models import ComplexityMetrics


class RadonAdapter:
    """Python 전용 복잡도 분석 (Radon).

    radon.complexity.cc_visit  → Cyclomatic Complexity (함수별 CC 평균)
    radon.metrics.h_visit      → Halstead 메트릭 (difficulty, volume)
    radon.metrics.mi_visit     → Maintainability Index (0~171, 0~100으로 클램핑)
    """

    def analyze(self, code: str) -> ComplexityMetrics:
        """Python 소스 코드의 복잡도 메트릭을 산출한다.

        Args:
            code: Python 소스 코드 문자열.

        Returns:
            ComplexityMetrics with CC, Halstead, MI.
            빈 코드이거나 파싱 불가 시 모든 수치가 0.0인 기본값을 반환한다.
        """
        from radon.complexity import cc_visit
        from radon.metrics import h_visit, mi_visit

        # --- Cyclomatic Complexity (함수/메서드 평균) ---
        try:
            cc_results = cc_visit(code)
            avg_cc = (
                sum(r.complexity for r in cc_results) / len(cc_results)
                if cc_results
                else 0.0
            )
        except SyntaxError:
            avg_cc = 0.0

        # --- Halstead Metrics ---
        # h_visit returns Halstead(total=HalsteadReport(...), functions=[...])
        # HalsteadReport fields: h1, h2, N1, N2, vocabulary, length,
        #   calculated_length, volume, difficulty, effort, time, bugs
        try:
            h_result = h_visit(code)
            # h_result.total is a HalsteadReport namedtuple
            h_total = h_result.total
            halstead_difficulty = float(h_total.difficulty) if h_total.difficulty else 0.0
            halstead_volume = float(h_total.volume) if h_total.volume else 0.0
        except SyntaxError:
            halstead_difficulty = 0.0
            halstead_volume = 0.0

        # --- Maintainability Index ---
        # mi_visit returns a float; can exceed 100 for trivially simple code.
        # The domain model enforces le=100, so we clamp to [0, 100].
        try:
            mi_raw = mi_visit(code, multi=False)
            mi = max(0.0, min(100.0, float(mi_raw)))
        except SyntaxError:
            mi = 0.0

        return ComplexityMetrics(
            cyclomatic_complexity=avg_cc,
            halstead_difficulty=halstead_difficulty,
            halstead_volume=halstead_volume,
            maintainability_index=mi,
            cognitive_complexity=0.0,  # Radon은 cognitive complexity 미지원
        )


class LizardAdapter:
    """다국어 복잡도 분석 (Lizard).

    Lizard는 확장자로 언어를 자동 감지한다.
    Python, JavaScript, TypeScript, Java, Go, C, C++ 지원.
    Halstead 및 Maintainability Index는 미지원 (0.0 반환).
    """

    def analyze(
        self,
        code: str,
        *,
        language: str | None = None,
        filename: str = "temp.py",
    ) -> ComplexityMetrics:
        """소스 코드의 Cyclomatic Complexity를 산출한다.

        Args:
            code: 소스 코드 문자열.
            language: 언어 힌트. 제공 시 filename 확장자를 자동 결정한다.
                      None이면 filename 확장자를 그대로 사용한다.
            filename: 가상 파일명. 확장자로 언어 감지 (language 우선).

        Returns:
            ComplexityMetrics with cyclomatic_complexity만 채워진 값.
            Halstead, MI, cognitive_complexity는 0.0.
        """
        import lizard

        # language 힌트가 있으면 적절한 filename으로 변환
        effective_filename = (
            self.filename_for_language(language) if language else filename
        )

        analysis = lizard.analyze_file.analyze_source_code(effective_filename, code)
        functions = analysis.function_list
        avg_cc = (
            sum(f.cyclomatic_complexity for f in functions) / len(functions)
            if functions
            else 0.0
        )

        return ComplexityMetrics(
            cyclomatic_complexity=avg_cc,
            halstead_difficulty=0.0,  # Lizard는 Halstead 미지원
            halstead_volume=0.0,
            maintainability_index=0.0,  # Lizard는 MI 미지원
            cognitive_complexity=0.0,
        )

    @staticmethod
    def filename_for_language(language: str) -> str:
        """언어명 → Lizard가 인식하는 확장자를 가진 가상 파일명을 반환한다.

        Args:
            language: 언어명 (소문자 권장).

        Returns:
            확장자가 포함된 가상 파일명. 알 수 없는 언어는 "temp.txt" 반환.
        """
        mapping: dict[str, str] = {
            "python": "temp.py",
            "javascript": "temp.js",
            "typescript": "temp.ts",
            "java": "Temp.java",
            "go": "temp.go",
            "c": "temp.c",
            "cpp": "temp.cpp",
        }
        return mapping.get(language.lower(), "temp.txt")
