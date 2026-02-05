#!/usr/bin/env python3
"""
Git URL 분석 로직 테스트 스크립트

사용법:
    # Docker 컨테이너 내에서 실행
    docker compose exec backend python scripts/test_git_analysis.py

    # 특정 URL로 테스트
    docker compose exec backend python scripts/test_git_analysis.py https://github.com/username/repo

테스트 항목:
    1. GitHubService - URL 파싱, 계정 타입 확인, 레포 정보
    2. CodeAnalyzer - PyDriller diff 추출, AST 분석
    3. 전체 파이프라인 통합 테스트
"""
import asyncio
import json
import sys
import logging
from pprint import pprint
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """섹션 구분선 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def print_json(data: dict, max_depth: int = 3):
    """JSON 데이터를 보기 좋게 출력"""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str)[:5000])
    if len(json.dumps(data, default=str)) > 5000:
        print("\n... (truncated)")


async def test_github_service(test_url: str):
    """GitHubService 단위 테스트"""
    print_section("1. GitHubService 테스트")

    from app.services.github_service import GitHubService
    from app.core.config import settings

    svc = GitHubService()

    # 1.1 GITHUB_TOKEN 확인
    print(f"[1.1] GITHUB_TOKEN 설정: {'✅ 있음' if settings.GITHUB_TOKEN else '❌ 없음 (API 제한 있을 수 있음)'}")
    print()

    # 1.2 URL 파싱 테스트
    print(f"[1.2] URL 파싱 테스트: {test_url}")
    repo_path = svc._parse_repo_path(test_url)
    owner = svc._extract_owner(test_url)
    print(f"  - repo_path: {repo_path}")
    print(f"  - owner: {owner}")
    print()

    # 1.3 계정 타입 확인
    if owner:
        print(f"[1.3] 계정 타입 확인: {owner}")
        account_info = await svc.get_account_type(owner)
        print(f"  - type: {account_info.get('type')}")
        print(f"  - name: {account_info.get('name')}")
        print(f"  - error: {account_info.get('error')}")
        print()

    # 1.4 레포 정보 조회
    print(f"[1.4] 레포 정보 조회")
    repo_info = await svc.get_repo_info(test_url)
    print_json(repo_info)
    print()

    # 1.5 레포 언어 비율
    print(f"[1.5] 레포 언어 비율")
    languages = await svc.get_repo_languages(test_url)
    if languages:
        total = sum(languages.values())
        for lang, bytes_count in sorted(languages.items(), key=lambda x: -x[1])[:5]:
            ratio = (bytes_count / total * 100) if total > 0 else 0
            print(f"  - {lang}: {ratio:.1f}% ({bytes_count:,} bytes)")
    else:
        print("  (언어 정보 없음)")
    print()

    # 1.6 기여자 목록
    print(f"[1.6] 상위 기여자 (5명)")
    contributors = await svc.get_repo_contributors(test_url, limit=5)
    for c in contributors:
        print(f"  - {c['username']}: {c['contributions']} commits ({c['type']})")
    print()

    # 1.7 후보자 username 추론
    print(f"[1.7] 후보자 username 추론")
    inference = await svc.infer_candidate_username([test_url])
    print(f"  - username: {inference.get('username')}")
    print(f"  - confidence: {inference.get('confidence')}")
    print(f"  - source: {inference.get('source')}")
    print(f"  - personal_repos: {inference.get('personal_repos')}")
    print(f"  - skipped_org_repos: {inference.get('skipped_org_repos')}")

    return {
        "account_type": account_info.get("type") if owner else None,
        "languages": languages,
        "inference": inference,
    }


async def test_code_analyzer(test_url: str, username: str | None = None):
    """CodeAnalyzer 단위 테스트"""
    print_section("2. CodeAnalyzer 테스트 (PyDriller + AST)")

    from app.services.code_analyzer import CodeAnalyzer

    analyzer = CodeAnalyzer()

    # 2.1 PyDriller 분석 (최근 1년, 상위 10개 커밋만)
    print(f"[2.1] PyDriller 분석 (최근 1년)")
    print(f"  - repo_url: {test_url}")
    print(f"  - author filter: {username or '(없음 - 모든 커밋)'}")
    print(f"  분석 중... (레포 클론 및 커밋 순회)")

    try:
        driller_result = await analyzer.analyze_with_pydriller(
            repo_url=test_url,
            job_id="test-job",
            author=username,
            since_years=1,
            file_types=[".py", ".js", ".ts", ".tsx"],
            extract_diff=True,
        )

        print(f"\n  [통계]")
        stats = driller_result.get("stats", {})
        print(f"  - total_commits: {stats.get('total_commits', 0)}")
        print(f"  - total_additions: {stats.get('total_additions', 0)}")
        print(f"  - total_deletions: {stats.get('total_deletions', 0)}")
        print(f"  - avg_complexity: {stats.get('avg_complexity', 0)}")

        print(f"\n  [분석된 파일 수]: {len(driller_result.get('files', []))}")
        print(f"  [커밋 diff 수]: {len(driller_result.get('commit_diffs', []))}")

        # 상위 5개 파일
        files = driller_result.get("files", [])[:5]
        if files:
            print(f"\n  [상위 파일 (복잡도 기준)]:")
            for f in files:
                print(f"    - {f.get('filename')}: complexity={f.get('complexity', 0)}, "
                      f"added={f.get('added', 0)}, deleted={f.get('deleted', 0)}")

        # 상위 3개 diff
        diffs = driller_result.get("commit_diffs", [])[:3]
        if diffs:
            print(f"\n  [상위 커밋 diff (복잡도×변경량)]:")
            for d in diffs:
                print(f"    - [{d.get('commit_hash')}] {d.get('file_path')}")
                print(f"      +{d.get('additions', 0)} -{d.get('deletions', 0)}, "
                      f"complexity={d.get('complexity', 0)}")
                if d.get('diff'):
                    # diff 미리보기 (최대 200자)
                    diff_preview = d['diff'][:200].replace('\n', '\\n')
                    print(f"      diff: {diff_preview}...")

    except Exception as e:
        print(f"  ❌ PyDriller 분석 실패: {e}")
        driller_result = {"files": [], "stats": {}, "commit_diffs": []}

    print()

    # 2.2 AST 분석
    print(f"[2.2] AST 분석 (Python)")
    files_for_ast = driller_result.get("files", [])[:10]

    if files_for_ast:
        ast_result = await analyzer.analyze_ast(files_for_ast, primary_language="Python")
        print(f"  - parser_used: {ast_result.get('parser_used')}")
        print(f"  - functions: {len(ast_result.get('functions', []))}")
        print(f"  - classes: {len(ast_result.get('classes', []))}")
        print(f"  - imports: {len(ast_result.get('imports', []))}")

        # 샘플 함수
        funcs = ast_result.get("functions", [])[:3]
        if funcs:
            print(f"\n  [샘플 함수]:")
            for fn in funcs:
                params = ", ".join(fn.get("params", []))
                print(f"    - {fn.get('name')}({params})")
    else:
        print("  (분석할 파일 없음)")
        ast_result = {}

    return {
        "driller_stats": driller_result.get("stats", {}),
        "file_count": len(driller_result.get("files", [])),
        "diff_count": len(driller_result.get("commit_diffs", [])),
        "ast_result": ast_result,
    }


async def test_jd_matching(test_url: str, jd_tech_stack: list[str]):
    """JD 매칭 레포 필터링 테스트"""
    print_section("3. JD 매칭 레포 필터링")

    from app.services.github_service import GitHubService

    svc = GitHubService()

    print(f"[3.1] JD 기술스택: {jd_tech_stack}")
    print(f"[3.2] 테스트 URL: {test_url}")
    print(f"[3.3] 최소 매칭 비율: 30%")
    print()

    matched = await svc.filter_repos_by_language(
        github_urls=[test_url],
        target_languages=jd_tech_stack,
        min_language_ratio=0.3,
    )

    if matched:
        print(f"✅ 매칭됨!")
        for m in matched:
            print(f"  - name: {m.get('name')}")
            print(f"  - jd_match_ratio: {m.get('jd_match_ratio', 0) * 100:.1f}%")
            print(f"  - languages: {m.get('languages')}")
    else:
        print(f"❌ 매칭되지 않음 (JD 기술스택과 레포 언어 불일치)")

    return matched


async def test_full_pipeline(test_url: str, jd_tech_stack: list[str]):
    """전체 analyze_code Activity 파이프라인 테스트"""
    print_section("4. 전체 파이프라인 테스트 (analyze_code Activity)")

    # Activity는 Temporal worker 컨텍스트에서만 실행 가능
    # 여기서는 내부 로직만 직접 호출

    from app.services.github_service import GitHubService
    from app.services.code_analyzer import CodeAnalyzer

    github = GitHubService()
    analyzer = CodeAnalyzer()

    print(f"[4.1] Phase 1: JD 매칭 레포 선별")
    target_repos = await github.filter_repos_by_language(
        github_urls=[test_url],
        target_languages=jd_tech_stack,
        min_language_ratio=0.3,
    )
    print(f"  - 매칭된 레포: {len(target_repos)}개")

    if not target_repos:
        print("  ⚠️ 매칭된 레포 없음. 파이프라인 종료.")
        return {"repositories": [], "top_question_candidates": []}

    # username 추론
    inference = await github.infer_candidate_username([test_url])
    candidate_username = inference.get("username")
    print(f"  - 추론된 username: {candidate_username}")

    repositories = []
    for repo_info in target_repos:
        repo_url = repo_info.get("url", test_url)
        repo_name = repo_info.get("name", "unknown")

        print(f"\n[4.2] Phase 2: PyDriller 분석 - {repo_name}")
        driller_result = await analyzer.analyze_with_pydriller(
            repo_url=repo_url,
            job_id="test-pipeline",
            author=candidate_username,
            since_years=1,
            file_types=[".py", ".js", ".ts"],
        )
        print(f"  - commits: {driller_result['stats'].get('total_commits', 0)}")
        print(f"  - additions: {driller_result['stats'].get('total_additions', 0)}")

        print(f"\n[4.3] Phase 3: AST 분석 - {repo_name}")
        primary_lang = max(repo_info.get("languages", {}), key=repo_info.get("languages", {}).get, default=None)
        top_files = analyzer.select_top_files(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            max_files=20,
        )
        ast_result = await analyzer.analyze_ast(files=top_files, primary_language=primary_lang)
        print(f"  - functions: {len(ast_result.get('functions', []))}")
        print(f"  - classes: {len(ast_result.get('classes', []))}")

        print(f"\n[4.4] Phase 4: LLM 분석 - {repo_name}")
        ranked_files = analyzer.rank_files_for_llm(
            files=driller_result["files"],
            jd_tech_stack=jd_tech_stack,
            token_budget=30_000,
        )
        print(f"  - LLM 분석 대상 파일: {len(ranked_files)}개")

        # LLM 호출은 비용이 발생하므로 스킵 옵션 제공
        print(f"  - ⚠️ LLM 호출은 스킵됨 (비용 절약). 실제 분석은 Langfuse에서 확인하세요.")

        repositories.append({
            "repo_url": repo_url,
            "repo_name": repo_name,
            "language": primary_lang,
            "candidate_commits": driller_result["stats"]["total_commits"],
            "candidate_additions": driller_result["stats"]["total_additions"],
            "avg_complexity": driller_result["stats"]["avg_complexity"],
            "ast_summary": {
                "functions": len(ast_result.get("functions", [])),
                "classes": len(ast_result.get("classes", [])),
            },
        })

    print_section("5. 최종 결과")
    print_json({
        "repositories": repositories,
        "combined_tech_stack": jd_tech_stack,
        "total_repos_analyzed": len(repositories),
    })

    return {
        "repositories": repositories,
        "top_question_candidates": [],
    }


async def main():
    """메인 테스트 실행"""
    print("\n" + "🔍 Git URL 분석 테스트 스크립트 🔍".center(60))
    print(f"실행 시간: {datetime.now().isoformat()}")

    # 테스트 URL 설정
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        # 기본 테스트 URL (공개 레포)
        test_url = "https://github.com/fastapi/fastapi"

    # JD 기술스택 (테스트용)
    jd_tech_stack = ["Python", "JavaScript", "TypeScript"]

    print(f"\n테스트 URL: {test_url}")
    print(f"JD 기술스택: {jd_tech_stack}")

    try:
        # 1. GitHubService 테스트
        github_result = await test_github_service(test_url)

        # 2. CodeAnalyzer 테스트
        username = github_result.get("inference", {}).get("username")
        analyzer_result = await test_code_analyzer(test_url, username)

        # 3. JD 매칭 테스트
        await test_jd_matching(test_url, jd_tech_stack)

        # 4. 전체 파이프라인 테스트
        await test_full_pipeline(test_url, jd_tech_stack)

        print_section("✅ 테스트 완료")
        print("Langfuse에서 상세 트레이스를 확인하세요:")
        print("  https://langfuse.mystery-place.com")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
