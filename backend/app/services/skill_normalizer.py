"""
backend/app/services/skill_normalizer.py
Hybrid 3-Tier Skill Normalizer — 스킬 정규화 서비스

Tier 1: Alias Lookup (O(1)) — skill_aliases 테이블 exact match
Tier 2: Embedding Similarity (O(log n)) — pgvector cosine search, 자기학습
Tier 3: LLM Classification (rare, O(초)) — 완전 새 스킬 분류

Anti-match protection: Java ≠ JavaScript, C ≠ C++ ≠ C# 등
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session as get_async_session_factory

logger = logging.getLogger(__name__)


@dataclass
class ResolvedSkill:
    """정규화된 스킬 결과"""
    canonical: str            # taxonomy의 canonical_name
    taxonomy_id: int | None = None
    confidence: float = 1.0   # 0.0-1.0
    method: str = "alias"     # "alias" | "embedding" | "llm" | "passthrough"
    category: str | None = None   # language/framework/tool/platform/concept
    domain: str | None = None     # frontend/backend/devops/ml/data
    original: str = ""        # 원본 입력값


@dataclass
class UnifiedResolvedSkill:
    """다중 소스에서 통합된 정규화 스킬"""
    canonical: str
    taxonomy_id: int | None = None
    aliases: list[str] = field(default_factory=list)   # 원본 스킬명들
    sources: list[str] = field(default_factory=list)    # ["resume", "github", "linkedin"]
    category: str | None = None
    domain: str | None = None
    confidence: float = 1.0
    implied_skills: list[str] = field(default_factory=list)  # taxonomy implies 관계
    proficiency_signals: dict = field(default_factory=dict)


# Anti-match pairs: 이 쌍들은 절대 같은 스킬로 매칭하면 안 됨
_ANTI_MATCH_PAIRS: set[frozenset[str]] = {
    frozenset({"java", "javascript"}),
    frozenset({"c", "c++"}),
    frozenset({"c", "c#"}),
    frozenset({"c++", "c#"}),
    frozenset({"go", "google"}),
    frozenset({"r", "rust"}),
    frozenset({"swift", "swiftui"}),
    frozenset({"vue", "vite"}),
    frozenset({"react", "react native"}),
}


def _is_anti_match(a: str, b: str) -> bool:
    """두 스킬이 anti-match 쌍인지 확인"""
    return frozenset({a.lower(), b.lower()}) in _ANTI_MATCH_PAIRS


class SkillNormalizer:
    """3-Tier 스킬 정규화 서비스"""

    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._alias_cache: dict[str, tuple[str, int, str, str]] | None = None  # alias → (canonical, id, category, domain)

    async def _get_session(self) -> AsyncSession:
        if self._session:
            return self._session
        return get_async_session_factory()

    async def _warm_alias_cache(self, session: AsyncSession):
        """alias 캐시 사전 로딩 (첫 호출 시 1회)"""
        if self._alias_cache is not None:
            return
        result = await session.execute(text("""
            SELECT sa.alias, st.canonical_name, st.id, st.category, st.domain
            FROM skill_aliases sa
            JOIN skill_taxonomy st ON sa.taxonomy_id = st.id
        """))
        self._alias_cache = {}
        for alias, canonical, tid, cat, dom in result.fetchall():
            self._alias_cache[alias.lower()] = (canonical, tid, cat, dom)
        logger.debug(f"Alias cache warmed: {len(self._alias_cache)} entries")

    async def resolve(self, raw_skill: str, session: AsyncSession | None = None) -> ResolvedSkill:
        """단일 스킬 정규화 (3-Tier)"""
        session = session or await self._get_session()
        normalized = raw_skill.lower().strip()

        if not normalized:
            return ResolvedSkill(canonical=raw_skill, confidence=0.0, method="passthrough", original=raw_skill)

        # Tier 1: Alias exact lookup
        await self._warm_alias_cache(session)
        if normalized in self._alias_cache:
            canonical, tid, cat, dom = self._alias_cache[normalized]
            return ResolvedSkill(
                canonical=canonical, taxonomy_id=tid,
                confidence=1.0, method="alias",
                category=cat, domain=dom,
                original=raw_skill,
            )

        # Tier 2: Embedding similarity (if pgvector available)
        emb_result = await self._embedding_search(session, raw_skill, threshold=0.85)
        if emb_result:
            # Anti-match protection
            if not _is_anti_match(normalized, emb_result.canonical.lower()):
                # Auto-learn: register as new alias
                await self._auto_register_alias(session, normalized, emb_result.taxonomy_id)
                emb_result.original = raw_skill
                return emb_result

        # Tier 3: Passthrough (LLM classification placeholder — not blocking pipeline)
        return ResolvedSkill(
            canonical=raw_skill,  # Keep original
            confidence=0.3,
            method="passthrough",
            original=raw_skill,
        )

    async def resolve_batch(self, skills: list[str], session: AsyncSession | None = None) -> list[ResolvedSkill]:
        """배치 정규화 — Tier 1 일괄 → 미매칭만 Tier 2/3"""
        session = session or await self._get_session()
        await self._warm_alias_cache(session)

        results = []
        tier2_pending = []

        for skill in skills:
            normalized = skill.lower().strip()
            if not normalized:
                results.append(ResolvedSkill(canonical=skill, confidence=0.0, method="passthrough", original=skill))
                continue

            if normalized in self._alias_cache:
                canonical, tid, cat, dom = self._alias_cache[normalized]
                results.append(ResolvedSkill(
                    canonical=canonical, taxonomy_id=tid,
                    confidence=1.0, method="alias",
                    category=cat, domain=dom,
                    original=skill,
                ))
            else:
                tier2_pending.append((len(results), skill))
                results.append(None)  # placeholder

        # Tier 2/3 for unresolved
        for idx, skill in tier2_pending:
            resolved = await self.resolve(skill, session)
            results[idx] = resolved

        return results

    async def unify_from_sources(
        self,
        source_skills: dict[str, list[str]],
        session: AsyncSession | None = None,
    ) -> list[UnifiedResolvedSkill]:
        """다중 소스 스킬을 정규화 + 중복 제거 + 통합

        Args:
            source_skills: {"resume": [...], "github": [...], "linkedin": [...], "cover_letter": [...]}

        Returns:
            중복 제거된 UnifiedResolvedSkill 리스트
        """
        session = session or await self._get_session()
        unified_map: dict[str, UnifiedResolvedSkill] = {}  # canonical → UnifiedResolvedSkill

        for source_name, skills in source_skills.items():
            if not skills:
                continue
            resolved_list = await self.resolve_batch(skills, session)

            for resolved in resolved_list:
                key = resolved.canonical.lower()
                if key in unified_map:
                    # 이미 존재 — 소스/alias 추가
                    existing = unified_map[key]
                    if source_name not in existing.sources:
                        existing.sources.append(source_name)
                    if resolved.original and resolved.original not in existing.aliases:
                        existing.aliases.append(resolved.original)
                    existing.confidence = max(existing.confidence, resolved.confidence)
                else:
                    # 새 스킬
                    implied = await self.get_implications(resolved.canonical, session) if resolved.taxonomy_id else []
                    unified_map[key] = UnifiedResolvedSkill(
                        canonical=resolved.canonical,
                        taxonomy_id=resolved.taxonomy_id,
                        aliases=[resolved.original] if resolved.original != resolved.canonical else [],
                        sources=[source_name],
                        category=resolved.category,
                        domain=resolved.domain,
                        confidence=resolved.confidence,
                        implied_skills=implied,
                    )

        return list(unified_map.values())

    async def get_implications(self, canonical: str, session: AsyncSession | None = None) -> list[str]:
        """스킬의 implies 관계 조회 — "React" → ["JavaScript"]"""
        session = session or await self._get_session()
        result = await session.execute(text("""
            SELECT t.canonical_name
            FROM skill_relationships sr
            JOIN skill_taxonomy s ON sr.source_id = s.id
            JOIN skill_taxonomy t ON sr.target_id = t.id
            WHERE s.canonical_name = :name AND sr.relation_type = 'implies'
        """), {"name": canonical})
        return [r[0] for r in result.fetchall()]

    async def get_category(self, canonical: str, session: AsyncSession | None = None) -> str | None:
        """스킬 카테고리 조회"""
        session = session or await self._get_session()
        await self._warm_alias_cache(session)
        normalized = canonical.lower()
        if normalized in self._alias_cache:
            return self._alias_cache[normalized][2]
        return None

    async def match_skills(
        self,
        candidate_skills: list[UnifiedResolvedSkill],
        jd_requirements: list[dict],
        session: AsyncSession | None = None,
    ) -> dict:
        """후보자 스킬 vs JD 요구 스킬 매칭

        Returns:
            {
                "matched": [{"jd_skill": ..., "candidate_skill": ..., "match_type": ...}],
                "gaps": [{"skill": ..., "category": ...}],
                "overlap_score": float,
                "details": dict,
            }
        """
        session = session or await self._get_session()

        # 후보자 스킬셋 (canonical + implied)
        candidate_canonical = set()
        for skill in candidate_skills:
            candidate_canonical.add(skill.canonical.lower())
            for imp in skill.implied_skills:
                candidate_canonical.add(imp.lower())

        matched = []
        gaps = []
        total_weight = 0.0
        matched_weight = 0.0

        for req in jd_requirements:
            skill_name = req.get("skill", "").strip()
            if not skill_name:
                continue
            category = req.get("category", "우대")

            # Determine weight
            weight = 1.0 if category in ("필수", "required", "must") else 0.5

            # Resolve JD skill
            jd_resolved = await self.resolve(skill_name, session)
            jd_canonical = jd_resolved.canonical.lower()

            total_weight += weight

            # Check if candidate has this skill (or implied)
            if jd_canonical in candidate_canonical:
                matched.append({
                    "jd_skill": skill_name,
                    "jd_canonical": jd_resolved.canonical,
                    "candidate_skill": jd_resolved.canonical,
                    "match_type": "exact" if jd_resolved.method == "alias" else "semantic",
                    "category": category,
                    "confidence": jd_resolved.confidence,
                })
                matched_weight += weight
            else:
                gaps.append({
                    "skill": skill_name,
                    "canonical": jd_resolved.canonical,
                    "category": category,
                })

        overlap = matched_weight / max(total_weight, 0.001)

        return {
            "matched": matched,
            "gaps": gaps,
            "overlap_score": overlap,
            "total_jd_skills": len(jd_requirements),
            "matched_count": len(matched),
            "gap_count": len(gaps),
        }

    async def _embedding_search(
        self,
        session: AsyncSession,
        raw_skill: str,
        threshold: float = 0.85,
    ) -> ResolvedSkill | None:
        """Tier 2: pgvector embedding similarity search"""
        try:
            # Check if sentence-transformers is available
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None

        try:
            # Load model (cached by sentence-transformers)
            model = SentenceTransformer("all-MiniLM-L6-v2")
            embedding = model.encode(raw_skill).tolist()

            result = await session.execute(text("""
                SELECT id, canonical_name, category, domain,
                       1 - (embedding <=> :emb::vector) AS similarity
                FROM skill_taxonomy
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> :emb::vector
                LIMIT 1
            """), {"emb": str(embedding)})

            row = result.fetchone()
            if row and row[4] >= threshold:
                return ResolvedSkill(
                    canonical=row[1],
                    taxonomy_id=row[0],
                    confidence=float(row[4]),
                    method="embedding",
                    category=row[2],
                    domain=row[3],
                )
        except Exception as e:
            logger.debug(f"Embedding search failed for '{raw_skill}': {e}")

        return None

    async def _auto_register_alias(self, session: AsyncSession, alias: str, taxonomy_id: int):
        """Tier 2 매칭 성공 시 alias 자동 등록 (자기학습)"""
        try:
            await session.execute(text("""
                INSERT INTO skill_aliases (taxonomy_id, alias, source)
                VALUES (:tid, :alias, 'auto_learned')
                ON CONFLICT (alias) DO NOTHING
            """), {"tid": taxonomy_id, "alias": alias.lower()})
            await session.commit()
            # Update cache
            if self._alias_cache is not None:
                result = await session.execute(
                    text("SELECT canonical_name, category, domain FROM skill_taxonomy WHERE id = :id"),
                    {"id": taxonomy_id},
                )
                row = result.fetchone()
                if row:
                    self._alias_cache[alias.lower()] = (row[0], taxonomy_id, row[1], row[2])
            logger.debug(f"Auto-learned alias: '{alias}' → taxonomy_id={taxonomy_id}")
        except Exception as e:
            logger.debug(f"Auto-register alias failed: {e}")
