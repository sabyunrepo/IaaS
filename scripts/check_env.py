#!/usr/bin/env python3
"""backend/worker 환경변수 정합성 검증 스크립트.

Usage:
    python scripts/check_env.py
    python scripts/check_env.py --strict  # 불일치 시 exit 1
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT / "docker-compose.yml"
ENV_EXAMPLE = ROOT / ".env.example"

# Worker에 의도적으로 없는 변수 (backend API 서버 전용)
BACKEND_ONLY_VARS = {
    "OAUTH_TOKEN_ENCRYPTION_KEY",
    "SESSION_SECRET",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GITHUB_CLIENT_ID",
    "GITHUB_CLIENT_SECRET",
    "FRONTEND_URL",
    "BACKEND_URL",
}

# Backend에 의도적으로 없는 변수 (worker 전용)
WORKER_ONLY_VARS = {
    "INTERNAL_API_URL",
}


def parse_env_block(content: str, service: str) -> dict[str, str]:
    """docker-compose.yml에서 특정 서비스의 environment 블록을 파싱한다."""
    env_vars: dict[str, str] = {}
    in_service = False
    in_env = False
    service_indent = 0

    for line in content.splitlines():
        stripped = line.lstrip()

        # 서비스 시작 감지 (최상위 레벨)
        if re.match(rf"^  {service}:", line):
            in_service = True
            service_indent = len(line) - len(stripped)
            continue

        if in_service:
            # 서비스 블록 벗어남 감지
            if stripped and not line.startswith(" " * (service_indent + 2)) and not stripped.startswith("#"):
                if not stripped.startswith("-"):
                    current_indent = len(line) - len(stripped)
                    if current_indent <= service_indent and not stripped.startswith("#"):
                        in_service = False
                        in_env = False
                        continue

            # environment 블록 시작
            if stripped == "environment:":
                in_env = True
                continue

            # environment 블록 내의 변수
            if in_env and stripped.startswith("- "):
                # 주석 라인은 스킵
                value = stripped[2:].strip()
                if value.startswith("#"):
                    continue
                # KEY=VALUE 형태 파싱
                match = re.match(r"^([A-Z_][A-Z0-9_]*)=(.*)$", value)
                if match:
                    env_vars[match.group(1)] = match.group(2)

            # environment 블록 끝 (다른 키워드 시작)
            elif in_env and stripped and not stripped.startswith("-") and not stripped.startswith("#"):
                in_env = False

    return env_vars


def parse_env_example(path: Path) -> set[str]:
    """`.env.example`에서 변수 이름 목록을 추출한다."""
    env_vars: set[str] = set()
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Z_][A-Z0-9_]*)=", stripped)
        if match:
            env_vars.add(match.group(1))
    return env_vars


def main() -> int:
    parser = argparse.ArgumentParser(description="backend/worker 환경변수 정합성 검증")
    parser.add_argument("--strict", action="store_true", help="불일치 시 exit 1")
    args = parser.parse_args()

    if not COMPOSE_FILE.exists():
        print(f"[ERROR] {COMPOSE_FILE} 파일을 찾을 수 없습니다.")
        return 1

    content = COMPOSE_FILE.read_text()
    backend_vars = parse_env_block(content, "backend")
    worker_vars = parse_env_block(content, "worker")

    print("=" * 60)
    print("  환경변수 정합성 검증 결과")
    print("=" * 60)
    print(f"\n  backend 변수: {len(backend_vars)}개")
    print(f"  worker  변수: {len(worker_vars)}개")

    # 1. backend에만 있는 변수 (의도적 제외 분류)
    backend_only = set(backend_vars.keys()) - set(worker_vars.keys())
    unexpected_backend_only = backend_only - BACKEND_ONLY_VARS

    print(f"\n{'─' * 60}")
    print("  [1] backend에만 있는 변수")
    print(f"{'─' * 60}")

    if backend_only & BACKEND_ONLY_VARS:
        print("  (의도적 제외 — API 서버 전용)")
        for var in sorted(backend_only & BACKEND_ONLY_VARS):
            print(f"    ✅ {var}")

    if unexpected_backend_only:
        print("  ⚠️  worker에 누락된 변수 (확인 필요)")
        for var in sorted(unexpected_backend_only):
            print(f"    ❌ {var} = {backend_vars[var]}")

    # 2. worker에만 있는 변수
    worker_only = set(worker_vars.keys()) - set(backend_vars.keys())
    unexpected_worker_only = worker_only - WORKER_ONLY_VARS

    print(f"\n{'─' * 60}")
    print("  [2] worker에만 있는 변수")
    print(f"{'─' * 60}")

    if worker_only & WORKER_ONLY_VARS:
        print("  (의도적 — worker 전용)")
        for var in sorted(worker_only & WORKER_ONLY_VARS):
            print(f"    ✅ {var}")

    if unexpected_worker_only:
        print("  ⚠️  backend에 누락된 변수 (확인 필요)")
        for var in sorted(unexpected_worker_only):
            print(f"    ❌ {var} = {worker_vars[var]}")

    # 3. 양쪽 모두 있지만 값이 다른 변수
    common_vars = set(backend_vars.keys()) & set(worker_vars.keys())
    value_mismatches = {
        var for var in common_vars if backend_vars[var] != worker_vars[var]
    }

    print(f"\n{'─' * 60}")
    print("  [3] 값이 다른 변수")
    print(f"{'─' * 60}")

    if value_mismatches:
        for var in sorted(value_mismatches):
            print(f"    ℹ️  {var}")
            print(f"       backend: {backend_vars[var]}")
            print(f"       worker:  {worker_vars[var]}")
    else:
        print("    ✅ 공통 변수 값 모두 일치")

    # 4. .env.example 검증
    if ENV_EXAMPLE.exists():
        env_example_vars = parse_env_example(ENV_EXAMPLE)
        # docker-compose에서 사용하는 ${VAR} 패턴의 변수명 추출
        compose_ref_vars: set[str] = set()
        for match in re.finditer(r"\$\{([A-Z_][A-Z0-9_]*)", content):
            compose_ref_vars.add(match.group(1))

        missing_in_example = compose_ref_vars - env_example_vars
        # 인프라 전용 변수 제외 (POSTGRES_USER 등은 docker-compose 내부용)
        infra_vars = {"POSTGRES_USER", "POSTGRES_DB"}
        missing_in_example -= infra_vars

        print(f"\n{'─' * 60}")
        print("  [4] .env.example 누락 변수")
        print(f"{'─' * 60}")

        if missing_in_example:
            for var in sorted(missing_in_example):
                print(f"    ⚠️  {var} — .env.example에 문서화 필요")
        else:
            print("    ✅ 모든 변수가 .env.example에 문서화됨")
    else:
        print(f"\n  ⚠️  {ENV_EXAMPLE} 파일 없음")

    # 결과 요약
    issues = len(unexpected_backend_only) + len(unexpected_worker_only)
    print(f"\n{'=' * 60}")
    if issues == 0:
        print("  ✅ 불일치 0건 — 정합성 검증 통과")
    else:
        print(f"  ⚠️  불일치 {issues}건 — 확인 필요")
    print(f"{'=' * 60}\n")

    if args.strict and issues > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
