#!/usr/bin/env python3
"""
scripts/create_test_job.py
테스트 Job 생성 스크립트 — 프론트엔드에서 확인 가능한 Job을 CLI로 생성합니다.

사용법:
    # 기본 테스트 Job (hoone0802@gmail.com 유저)
    docker compose exec backend python scripts/create_test_job.py

    # 커스텀 옵션
    docker compose exec backend python scripts/create_test_job.py \
        --email hoone0802@gmail.com \
        --level "CTO/VP" \
        --lang en \
        --questions 20 \
        --linkedin "https://www.linkedin.com/in/byun-sanghoon-303918338/" \
        --github "https://github.com/sabyunrepo"

    # JD 파일에서 읽기
    docker compose exec backend python scripts/create_test_job.py --jd-file /path/to/jd.txt

    # Dry run (미리보기)
    docker compose exec backend python scripts/create_test_job.py --dry-run
"""
import argparse
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


DEFAULT_JD = """주요업무
• AI 활용 서비스 개발 : 기존 AI 서비스 고도화 및 LLM을 활용한 신규 AI 서비스를 직접 개발하고, 프롬프트 엔지니어링 및 성능 최적화를 책임집니다.
• AI 모델 백엔드 구축 및 애플리케이션 연동 : AI 모델을 상용 애플리케이션과 효율적으로 연동하고 AI 서비스의 백엔드 아키텍처를 설계하며 안정적인 운영과 지속적인 개선을 담당합니다.
• 제공 기술 및 서비스 문서화 : 개발된 AI 기술과 서비스에 대한 명확하고 상세한 문서를 작성하여, 전사 조직에 지식 공유를 활성화하고 효율적인 협업을 지원합니다.
자격요건
• 관련 경력 3년 이상 또는 그에 준하는 뛰어난 역량을 갖추신 분
• LLM API 활용 경험이 있거나, 생성형 AI 서비스를 개발해 본 경험이 있는 분
• AI 모델 백엔드 구축 경험이 있으며, AI 기술을 실제 상용 서비스에 적용한 경험이 있는 분
• Python 과 Typescript 를 활용한 API 개발 및 대규모 데이터 처리 로직 구현에 능숙하신 분
우대사항
• AI 모델 Fine-tuning 경험이 있거나, 사전 학습된 모델을 특정 도메인에 최적화한 경험이 있으신 분
• 대규모 AI 서비스 운영 경험이 있으며, AI 서비스의 안정성과 성능을 극대화한 경험이 있으신 분
• AI 성능 최적화 경험이 있거나, 추론 속도와 비용 효율성을 개선한 경험이 있으신 분
• 새로운 기술 트렌드에 대한 깊은 관심과 함께, 신기술 도입 및 적용에 적극적으로 참여하고자 하는 열정이 있으신 분
• 대규모 AI 서비스 및 트래픽을 안정적으로 처리할 수 있는 아키텍처를 설계하고 운영해 본 경험이 있으신 분
• 제공하는 서비스에 대한 적극적인 기술 가이드 제공 경험이 있거나, 이를 통해 동료들의 성장을 돕는 것을 좋아하시는 분
• 개발 과정에서의 문서화의 중요성을 이해하고, 명확하고 체계적인 문서 작성을 통해 지식 공유와 협업에 기여할 수 있는 분"""

DEFAULT_EMAIL = "hoone0802@gmail.com"
DEFAULT_LINKEDIN = "https://www.linkedin.com/in/byun-sanghoon-303918338/"
DEFAULT_GITHUB = "https://github.com/sabyunrepo"

VALID_LEVELS = ["신입", "주니어", "미들", "시니어", "CTO/VP"]


async def create_job(args):
    """DB에 직접 Job을 생성하고 Temporal 워크플로우를 트리거합니다."""
    from sqlalchemy import select
    from app.core.database import async_session
    from app.models.database import UserDB
    from app.services.job_service import create_job as create_job_fn

    # JD 텍스트 결정
    if args.jd_file:
        jd_path = Path(args.jd_file)
        if not jd_path.exists():
            print(f"Error: JD file not found: {jd_path}")
            sys.exit(1)
        jd_text = jd_path.read_text(encoding="utf-8").strip()
    elif args.jd:
        jd_text = args.jd
    else:
        jd_text = DEFAULT_JD

    # input_data 구성
    input_data = {
        "jd_text": jd_text,
        "experience_level": args.level,
        "max_questions": args.questions,
        "include_expected_answers": True,
        "language_config": {
            "output_language": args.lang,
            "terminology_languages": ["ko", "en"],
        },
    }

    if args.linkedin:
        input_data["linkedin_url"] = args.linkedin
    if args.github:
        input_data["git_url"] = args.github

    # Dry run
    if args.dry_run:
        print("\n=== DRY RUN ===\n")
        print(f"Email: {args.email}")
        print(f"Level: {args.level}")
        print(f"Language: {args.lang}")
        print(f"Questions: {args.questions}")
        print(f"LinkedIn: {args.linkedin or 'N/A'}")
        print(f"GitHub: {args.github or 'N/A'}")
        print(f"JD length: {len(jd_text)} chars")
        print(f"JD preview: {jd_text[:100]}...")
        return

    # DB에서 유저 조회
    async with async_session() as db:
        result = await db.execute(
            select(UserDB).where(UserDB.email == args.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"Error: User not found: {args.email}")
            print("Available users:")
            all_users = await db.execute(select(UserDB.email))
            for row in all_users:
                print(f"  - {row[0]}")
            sys.exit(1)

        print(f"User: {user.email} (id: {user.id})")
        print(f"Level: {args.level}")
        print(f"Language: {args.lang}")
        print(f"Questions: {args.questions}")

        # Job 생성 (Temporal 워크플로우 자동 트리거)
        job = await create_job_fn(
            user_id=user.id,
            input_data=input_data,
            db=db,
        )
        await db.commit()

        print(f"\n✓ Job created: {job.id}")
        print(f"  Status: {job.status}")
        print(f"  Created: {job.created_at}")
        print(f"\n  프론트엔드에서 확인: http://localhost/jobs/{job.id}")


def main():
    parser = argparse.ArgumentParser(
        description="Create a test job for frontend verification"
    )
    parser.add_argument(
        "--email", "-e",
        default=DEFAULT_EMAIL,
        help=f"User email (default: {DEFAULT_EMAIL})",
    )
    parser.add_argument(
        "--level", "-l",
        default="CTO/VP",
        choices=VALID_LEVELS,
        help="Experience level (default: CTO/VP)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Output language (default: en)",
    )
    parser.add_argument(
        "--questions", "-q",
        type=int,
        default=20,
        help="Max questions (default: 20)",
    )
    parser.add_argument(
        "--linkedin",
        default=DEFAULT_LINKEDIN,
        help="LinkedIn URL",
    )
    parser.add_argument(
        "--github",
        default=DEFAULT_GITHUB,
        help="GitHub URL",
    )
    parser.add_argument(
        "--jd",
        help="JD text (inline)",
    )
    parser.add_argument(
        "--jd-file",
        help="Path to JD text file",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview without creating",
    )

    args = parser.parse_args()

    if args.level not in VALID_LEVELS:
        print(f"Error: Invalid level '{args.level}'. Must be one of: {VALID_LEVELS}")
        sys.exit(1)

    asyncio.run(create_job(args))


if __name__ == "__main__":
    main()
