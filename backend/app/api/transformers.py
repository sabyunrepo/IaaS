"""
backend/app/api/transformers.py
API 응답 포맷 변환기 (v1 ↔ v2)
"""
from typing import Any


def transform_to_v1_format(script: dict) -> dict:
    """v2 → v1 포맷 변환 (하위 호환)

    v2의 scenarios 배열 → v1의 evaluation_scenarios 객체
    v2의 follow_up good/poor 객체 → v1의 scoring 객체
    """
    v1_script = {**script}

    # Remove v2-only fields
    v1_script.pop("intel", None)
    v1_script.pop("analysis", None)
    v1_script.pop("decision", None)
    v1_script.pop("category_weights", None)
    v1_script.pop("candidate", None)

    questions = v1_script.get("questions", [])
    for q in questions:
        # v2 scenarios 배열 → v1 evaluation_scenarios 객체
        scenarios = q.pop("scenarios", [])
        if scenarios and not q.get("evaluation_scenarios"):
            evaluation_scenarios = {
                "expert": {},
                "mid": {},
                "low": {},
            }
            for s in scenarios:
                level = s.get("level", "").lower()
                if level in evaluation_scenarios:
                    evaluation_scenarios[level] = {
                        "description": s.get("text", ""),
                        "indicators": [],
                        "score": s.get("score", 0),
                    }
            q["evaluation_scenarios"] = evaluation_scenarios

        # v2 title → v1 topic (기존 topic이 없는 경우)
        if "title" in q and not q.get("topic"):
            q["topic"] = q.pop("title")

        # v2 answer_keywords (question level) → v1 expected_answer.answer_keywords
        if "answer_keywords" in q:
            answer_keywords = q.pop("answer_keywords")
            if q.get("expected_answer"):
                if not q["expected_answer"].get("answer_keywords"):
                    q["expected_answer"]["answer_keywords"] = answer_keywords

        # v2 follow_ups good/poor → v1 scoring
        for fu in q.get("follow_ups", []):
            good = fu.pop("good", None)
            poor = fu.pop("poor", None)
            trigger = fu.pop("trigger", None)

            # trigger (v2) → trigger_level (v1)
            if trigger and not fu.get("trigger_level"):
                fu["trigger_level"] = trigger.lower()

            # good/poor 객체 → scoring 객체
            if good and poor and not fu.get("scoring"):
                fu["scoring"] = {
                    "good": good.get("text", ""),
                    "good_score": good.get("score", 0),
                    "poor": poor.get("text", ""),
                    "poor_score": poor.get("score", 0),
                }

        # Remove v2-only fields from question
        q.pop("is_risk", None)

    return v1_script


def transform_to_v2_format(script: dict) -> dict:
    """v1 → v2 포맷 변환

    v1의 evaluation_scenarios 객체 → v2의 scenarios 배열
    v1의 scoring 객체 → v2의 good/poor 객체
    """
    v2_script = {**script}

    questions = v2_script.get("questions", [])
    for q in questions:
        # v1 evaluation_scenarios 객체 → v2 scenarios 배열
        eval_scenarios = q.get("evaluation_scenarios", {})
        if eval_scenarios and not q.get("scenarios"):
            scenarios = []
            level_map = {"expert": "Expert", "mid": "Mid", "low": "Low"}
            for level_key, level_data in eval_scenarios.items():
                if isinstance(level_data, dict):
                    scenarios.append({
                        "level": level_map.get(level_key, level_key.capitalize()),
                        "score": level_data.get("score", 0),
                        "text": level_data.get("description", ""),
                        "depth_expectations": "",
                    })
            q["scenarios"] = sorted(
                scenarios,
                key=lambda x: {"Expert": 0, "Mid": 1, "Low": 2}.get(x["level"], 3)
            )

        # v1 topic → v2 title
        if q.get("topic") and not q.get("title"):
            q["title"] = q["topic"]

        # v1 expected_answer.answer_keywords → v2 answer_keywords (question level)
        expected = q.get("expected_answer", {})
        if expected and expected.get("answer_keywords") and not q.get("answer_keywords"):
            q["answer_keywords"] = expected["answer_keywords"]

        # v1 follow_ups scoring → v2 good/poor
        for fu in q.get("follow_ups", []):
            scoring = fu.get("scoring", {})
            trigger_level = fu.get("trigger_level")

            # trigger_level (v1) → trigger (v2)
            if trigger_level and not fu.get("trigger"):
                fu["trigger"] = trigger_level.capitalize()

            # scoring 객체 → good/poor 객체
            if scoring and not fu.get("good"):
                fu["good"] = {
                    "text": scoring.get("good", ""),
                    "score": scoring.get("good_score", 0),
                }
                fu["poor"] = {
                    "text": scoring.get("poor", ""),
                    "score": scoring.get("poor_score", 0),
                }

        # Add default is_risk field
        if "is_risk" not in q:
            category = q.get("category", "")
            q["is_risk"] = category == "risk_flags" or "risk" in category.lower()

    # Ensure candidate alias exists
    if v2_script.get("candidate_summary") and not v2_script.get("candidate"):
        v2_script["candidate"] = v2_script["candidate_summary"]

    return v2_script


def ensure_compatible_format(script: dict, version: str = "v2") -> dict:
    """요청된 버전에 맞게 스크립트 포맷 보장"""
    if version == "v1":
        return transform_to_v1_format(script)
    else:
        return transform_to_v2_format(script)
