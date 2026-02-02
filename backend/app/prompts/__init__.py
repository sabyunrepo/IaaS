"""
backend/app/prompts/__init__.py
YAML 프롬프트 템플릿 로더
"""
import os
from functools import lru_cache

import yaml

PROMPTS_DIR = os.path.dirname(__file__)


@lru_cache(maxsize=32)
def _load_yaml(filename: str) -> dict:
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prompt(filename: str, key: str, **kwargs) -> str:
    """YAML에서 프롬프트 템플릿을 로드하고 변수를 치환합니다.

    Args:
        filename: YAML 파일명 (예: "jd_analysis.yaml")
        key: 프롬프트 키 (예: "analyze")
        **kwargs: 템플릿 변수
    """
    data = _load_yaml(filename)
    template = data["prompts"][key]["template"]
    return template.format(**kwargs)
