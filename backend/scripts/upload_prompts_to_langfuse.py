#!/usr/bin/env python3
"""
scripts/upload_prompts_to_langfuse.py
로컬 YAML 프롬프트를 Langfuse Prompt Management에 업로드합니다.

사용법:
    # 모든 프롬프트 업로드
    docker compose exec backend python scripts/upload_prompts_to_langfuse.py

    # 특정 파일만 업로드
    docker compose exec backend python scripts/upload_prompts_to_langfuse.py --file question_generation.yaml

    # Dry run (미리보기)
    docker compose exec backend python scripts/upload_prompts_to_langfuse.py --dry-run

    # Production 라벨 추가
    docker compose exec backend python scripts/upload_prompts_to_langfuse.py --production
"""
import argparse
import os
import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml


# Note: YAML 템플릿이 이제 Mustache 문법 ({{variable}})을 직접 사용하므로
# 별도의 변환이 필요 없습니다. Langfuse와 YAML fallback 모두 동일한 문법 사용.


# =============================================================================
# Activity별 최적 모델 설정 (llm_config.py와 동기화)
# =============================================================================
# 모델 선택 기준:
# - 복잡한 추론/정확성 필요: openai:gpt-4o, anthropic:claude-3-5-sonnet
# - 단순 작업/비용 최적화: Z.AI GLM (glm-4.5-flash: 무료!)
# - 코드 분석 최적화: Z.AI GLM-4.7 (플래그십)
# =============================================================================

# Z.AI GLM 모델 (Zhipu AI)
# glm-4.5-flash: 무료! 단순 작업에 최적
# glm-4.5-air: $0.20/1M input, $1.10/1M output
# glm-4.7: $0.60/1M input, $2.20/1M output (최신 플래그십)
GLM_CHAT_MODEL = "zai/glm-4.5-flash"  # 무료 모델
GLM_CODER_MODEL = "zai/glm-4.7"  # 코드 분석용 플래그십

ACTIVITY_MODEL_CONFIG = {
    # Phase 0: Input Enrichment - 빠른 처리, GLM으로 비용 절감
    "enrich_input": {"model": GLM_CHAT_MODEL, "temperature": 0.3},

    # Phase 1: Planning - 중요 의사결정은 GPT-4o 유지
    "select_topics": {"model": "openai:gpt-4o", "temperature": 0.7},

    # Phase 2: Analysis
    "analyze_documents": {"model": "openai:gpt-4o", "temperature": 0.5},  # 문서 분석은 품질 중요
    "analyze_code": {"model": GLM_CODER_MODEL, "temperature": 0.5},  # 코드 분석은 GLM Coder
    "analyze_jd": {"model": GLM_CHAT_MODEL, "temperature": 0.3},  # JD 분석은 GLM Chat

    # Phase 2: HYBRID 3-Stage 코드 분석 (GLM Coder 모델)
    "code_overview_analysis": {"model": GLM_CODER_MODEL, "temperature": 0.3},
    "code_deep_analysis": {"model": GLM_CODER_MODEL, "temperature": 0.5},
    "code_synthesis_analysis": {"model": GLM_CODER_MODEL, "temperature": 0.5},

    # Phase 3: Question Generation (v2 format)
    "craft_question": {"model": "openai:gpt-4o", "temperature": 0.7},  # 핵심 품질 유지
    "enhance_terminology": {"model": GLM_CHAT_MODEL, "temperature": 0.5},  # 단순 작업 GLM
    "craft_evaluation_scenarios": {"model": "openai:gpt-4o", "temperature": 0.6},
    "design_follow_ups": {"model": GLM_CHAT_MODEL, "temperature": 0.7},  # 단순 작업 GLM
    "generate_interviewer_notes": {"model": GLM_CHAT_MODEL, "temperature": 0.5},  # 단순 작업 GLM
    "generate_decision_guide": {"model": "openai:gpt-4o", "temperature": 0.5},
    "revise_questions": {"model": GLM_CHAT_MODEL, "temperature": 0.5},  # 단순 작업 GLM

    # Phase 4: Finalization
    "quality_review": {"model": "openai:gpt-4o", "temperature": 0.3},  # 품질 검토는 GPT-4o
    "finalize_candidate_summary": {"model": "openai:gpt-4o", "temperature": 0.5},
    "finalize_interviewer_guide": {"model": GLM_CHAT_MODEL, "temperature": 0.5},  # GLM

    # Phase 4c: v2 Intel/Analysis Generation
    "generate_intel_brief": {"model": "openai:gpt-4o", "temperature": 0.5},
    "generate_deep_analysis": {"model": "openai:gpt-4o", "temperature": 0.5},
    "generate_decision_support": {"model": "openai:gpt-4o", "temperature": 0.5},
}

# YAML 키 → Activity 이름 매핑
YAML_TO_ACTIVITY = {
    ("document_analysis.yaml", "extract_profile"): "analyze_documents",
    ("jd_analysis.yaml", "analyze"): "analyze_jd",
    ("quality_review.yaml", "review"): "quality_review",
    ("finalization.yaml", "candidate_summary"): "finalize_candidate_summary",
    ("finalization.yaml", "interviewer_guide"): "finalize_interviewer_guide",
}


def get_activity_name(filename: str, key: str) -> str:
    """YAML 파일명과 키로 Activity 이름 결정"""
    mapping_key = (filename, key)
    if mapping_key in YAML_TO_ACTIVITY:
        return YAML_TO_ACTIVITY[mapping_key]
    return key


def get_langfuse_name(filename: str, key: str) -> str:
    """Langfuse 프롬프트 이름 생성"""
    base = filename.replace(".yaml", "")
    return f"{base}_{key}"


def load_yaml_prompts(prompts_dir: Path, filename: str | None = None) -> dict:
    """YAML 파일에서 프롬프트 로드"""
    prompts = {}

    files = [filename] if filename else os.listdir(prompts_dir)

    for fname in files:
        if not fname.endswith(".yaml"):
            continue

        filepath = prompts_dir / fname
        if not filepath.exists():
            print(f"Warning: {filepath} not found, skipping")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for key, prompt_data in data.get("prompts", {}).items():
            langfuse_name = get_langfuse_name(fname, key)
            activity_name = get_activity_name(fname, key)
            config = ACTIVITY_MODEL_CONFIG.get(activity_name, {
                "model": "openai:gpt-4o",
                "temperature": 0.5,
            })

            # YAML 템플릿이 이미 Mustache 문법 사용 - 변환 불필요
            prompts[langfuse_name] = {
                "name": langfuse_name,
                "template": prompt_data["template"],
                "description": prompt_data.get("description", ""),
                "config": config,
                "source_file": fname,
                "source_key": key,
                "activity_name": activity_name,
            }

    return prompts


def upload_to_langfuse(
    prompts: dict,
    dry_run: bool = False,
    production: bool = False,
):
    """Langfuse에 프롬프트 업로드"""
    from langfuse import Langfuse

    if dry_run:
        print("\n=== DRY RUN MODE ===\n")
        for name, data in prompts.items():
            print(f"Would upload: {name}")
            print(f"  Source: {data['source_file']}:{data['source_key']}")
            print(f"  Activity: {data['activity_name']}")
            print(f"  Model: {data['config'].get('model')}")
            print(f"  Temperature: {data['config'].get('temperature')}")
            print(f"  Template length: {len(data['template'])} chars")

            # Show detected Langfuse variables
            variables = re.findall(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}', data['template'])
            if variables:
                print(f"  Variables: {', '.join(sorted(set(variables)))}")
            print()
        return

    # Initialize Langfuse client
    client = Langfuse()
    print(f"Connected to Langfuse")

    labels = ["production"] if production else []

    uploaded = 0
    errors = 0

    for name, data in prompts.items():
        try:
            # Check if prompt already exists
            try:
                existing = client.get_prompt(name)
                print(f"Updating existing prompt: {name} (current version: {existing.version})")
            except Exception:
                print(f"Creating new prompt: {name}")

            # Create or update prompt
            client.create_prompt(
                name=name,
                type="text",
                prompt=data["template"],
                config=data["config"],
                labels=labels,
            )

            print(f"  ✓ Uploaded: {name} (model: {data['config'].get('model')})")
            uploaded += 1

        except Exception as e:
            print(f"  ✗ Error uploading {name}: {e}")
            errors += 1

    print(f"\n=== Summary ===")
    print(f"Uploaded: {uploaded}")
    print(f"Errors: {errors}")

    # Flush to ensure all data is sent
    client.flush()


def main():
    parser = argparse.ArgumentParser(
        description="Upload YAML prompts to Langfuse Prompt Management"
    )
    parser.add_argument(
        "--file", "-f",
        help="Specific YAML file to upload (e.g., question_generation.yaml)",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview what would be uploaded without actually uploading",
    )
    parser.add_argument(
        "--production", "-p",
        action="store_true",
        help="Add 'production' label to uploaded prompts",
    )
    parser.add_argument(
        "--prompts-dir",
        default=str(Path(__file__).parent.parent / "app" / "prompts"),
        help="Directory containing YAML prompt files",
    )

    args = parser.parse_args()

    prompts_dir = Path(args.prompts_dir)
    if not prompts_dir.exists():
        print(f"Error: Prompts directory not found: {prompts_dir}")
        sys.exit(1)

    print(f"Loading prompts from: {prompts_dir}")
    prompts = load_yaml_prompts(prompts_dir, args.file)

    if not prompts:
        print("No prompts found to upload")
        sys.exit(1)

    print(f"Found {len(prompts)} prompts\n")

    upload_to_langfuse(
        prompts,
        dry_run=args.dry_run,
        production=args.production,
    )


if __name__ == "__main__":
    main()
