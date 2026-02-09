"""
backend/scripts/load_skill_taxonomy.py
MIND Tech Ontology → skill_taxonomy DB 로더

Usage:
    docker compose exec backend python scripts/load_skill_taxonomy.py
    docker compose exec backend python scripts/load_skill_taxonomy.py --seed-only  # MIND 없이 핵심 스킬만

Sources:
    - MIND Tech Ontology: https://github.com/MIND-TechAI/MIND-tech-ontology
    - 3,333 tech skills, 974 concepts, 10,897 relationships
    - MIT License, JSON format
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import httpx
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# MIND Tech Ontology GitHub raw URL
MIND_ONTOLOGY_URL = "https://raw.githubusercontent.com/MIND-TechAI/MIND-tech-ontology/main/ontology/tech-ontology.json"
MIND_CACHE_PATH = Path(__file__).parent / "data" / "tech-ontology.json"

# Domain mapping from MIND categories
DOMAIN_MAP = {
    "frontend": "frontend",
    "backend": "backend",
    "web": "frontend",
    "mobile": "frontend",
    "database": "backend",
    "devops": "devops",
    "cloud": "devops",
    "infrastructure": "devops",
    "ml": "ml",
    "machine_learning": "ml",
    "ai": "ml",
    "data": "data",
    "data_science": "data",
    "security": "security",
    "testing": "testing",
    "design": "design",
}

# Category mapping
CATEGORY_MAP = {
    "programming_language": "language",
    "language": "language",
    "framework": "framework",
    "library": "framework",
    "tool": "tool",
    "platform": "platform",
    "database": "tool",
    "concept": "concept",
    "methodology": "concept",
    "protocol": "concept",
}

# Fallback: Core skills seed data (if MIND download fails)
CORE_SKILLS_SEED = [
    # Languages
    {"name": "Python", "category": "language", "domain": "backend", "aliases": ["python3", "py"]},
    {"name": "JavaScript", "category": "language", "domain": "frontend", "aliases": ["js", "ecmascript", "es6", "es2015"]},
    {"name": "TypeScript", "category": "language", "domain": "frontend", "aliases": ["ts"]},
    {"name": "Java", "category": "language", "domain": "backend", "aliases": ["java8", "java11", "java17", "jdk"]},
    {"name": "Go", "category": "language", "domain": "backend", "aliases": ["golang"]},
    {"name": "Rust", "category": "language", "domain": "backend", "aliases": ["rust-lang"]},
    {"name": "C++", "category": "language", "domain": "backend", "aliases": ["cpp", "c plus plus"]},
    {"name": "C#", "category": "language", "domain": "backend", "aliases": ["csharp", "c sharp", "dotnet"]},
    {"name": "Ruby", "category": "language", "domain": "backend", "aliases": ["rb"]},
    {"name": "PHP", "category": "language", "domain": "backend", "aliases": ["php8"]},
    {"name": "Swift", "category": "language", "domain": "frontend", "aliases": ["swiftui"]},
    {"name": "Kotlin", "category": "language", "domain": "frontend", "aliases": ["kt"]},
    {"name": "Scala", "category": "language", "domain": "backend", "aliases": []},
    {"name": "R", "category": "language", "domain": "data", "aliases": ["r-lang", "rlang"]},
    {"name": "SQL", "category": "language", "domain": "data", "aliases": ["structured query language"]},
    {"name": "Shell", "category": "language", "domain": "devops", "aliases": ["bash", "sh", "zsh"]},
    {"name": "Lua", "category": "language", "domain": "backend", "aliases": []},
    {"name": "Dart", "category": "language", "domain": "frontend", "aliases": []},
    {"name": "Elixir", "category": "language", "domain": "backend", "aliases": []},
    {"name": "Haskell", "category": "language", "domain": "backend", "aliases": []},
    {"name": "Clojure", "category": "language", "domain": "backend", "aliases": ["clj"]},
    # Frontend Frameworks
    {"name": "React", "category": "framework", "domain": "frontend", "aliases": ["react.js", "reactjs", "react js"]},
    {"name": "Vue.js", "category": "framework", "domain": "frontend", "aliases": ["vue", "vuejs", "vue 3", "vue3"]},
    {"name": "Angular", "category": "framework", "domain": "frontend", "aliases": ["angularjs", "angular 2+"]},
    {"name": "Next.js", "category": "framework", "domain": "frontend", "aliases": ["nextjs", "next"]},
    {"name": "Nuxt.js", "category": "framework", "domain": "frontend", "aliases": ["nuxtjs", "nuxt"]},
    {"name": "Svelte", "category": "framework", "domain": "frontend", "aliases": ["sveltekit"]},
    {"name": "Tailwind CSS", "category": "framework", "domain": "frontend", "aliases": ["tailwind", "tailwindcss"]},
    {"name": "Bootstrap", "category": "framework", "domain": "frontend", "aliases": ["bootstrap5"]},
    {"name": "jQuery", "category": "framework", "domain": "frontend", "aliases": ["jquery"]},
    # Backend Frameworks
    {"name": "FastAPI", "category": "framework", "domain": "backend", "aliases": ["fast api", "fast-api"]},
    {"name": "Django", "category": "framework", "domain": "backend", "aliases": ["django rest framework", "drf"]},
    {"name": "Flask", "category": "framework", "domain": "backend", "aliases": []},
    {"name": "Spring Boot", "category": "framework", "domain": "backend", "aliases": ["spring", "spring framework", "springboot"]},
    {"name": "Express.js", "category": "framework", "domain": "backend", "aliases": ["express", "expressjs"]},
    {"name": "NestJS", "category": "framework", "domain": "backend", "aliases": ["nest.js", "nest"]},
    {"name": "Ruby on Rails", "category": "framework", "domain": "backend", "aliases": ["rails", "ror"]},
    {"name": "ASP.NET", "category": "framework", "domain": "backend", "aliases": ["asp.net core", "aspnet", "dotnet core"]},
    {"name": "Laravel", "category": "framework", "domain": "backend", "aliases": []},
    {"name": "Gin", "category": "framework", "domain": "backend", "aliases": ["gin-gonic"]},
    # Mobile
    {"name": "React Native", "category": "framework", "domain": "frontend", "aliases": ["rn", "react-native"]},
    {"name": "Flutter", "category": "framework", "domain": "frontend", "aliases": []},
    # Databases
    {"name": "PostgreSQL", "category": "tool", "domain": "data", "aliases": ["postgres", "psql", "pg"]},
    {"name": "MySQL", "category": "tool", "domain": "data", "aliases": ["mariadb"]},
    {"name": "MongoDB", "category": "tool", "domain": "data", "aliases": ["mongo"]},
    {"name": "Redis", "category": "tool", "domain": "data", "aliases": []},
    {"name": "Elasticsearch", "category": "tool", "domain": "data", "aliases": ["elastic", "es"]},
    {"name": "SQLite", "category": "tool", "domain": "data", "aliases": []},
    {"name": "DynamoDB", "category": "tool", "domain": "data", "aliases": ["dynamo"]},
    {"name": "Cassandra", "category": "tool", "domain": "data", "aliases": []},
    {"name": "Neo4j", "category": "tool", "domain": "data", "aliases": []},
    # DevOps & Cloud
    {"name": "Docker", "category": "tool", "domain": "devops", "aliases": ["docker-compose", "dockerfile"]},
    {"name": "Kubernetes", "category": "tool", "domain": "devops", "aliases": ["k8s", "kube"]},
    {"name": "AWS", "category": "platform", "domain": "devops", "aliases": ["amazon web services"]},
    {"name": "Google Cloud Platform", "category": "platform", "domain": "devops", "aliases": ["gcp", "google cloud"]},
    {"name": "Microsoft Azure", "category": "platform", "domain": "devops", "aliases": ["azure"]},
    {"name": "Terraform", "category": "tool", "domain": "devops", "aliases": ["tf"]},
    {"name": "Jenkins", "category": "tool", "domain": "devops", "aliases": []},
    {"name": "GitHub Actions", "category": "tool", "domain": "devops", "aliases": ["gh actions"]},
    {"name": "GitLab CI/CD", "category": "tool", "domain": "devops", "aliases": ["gitlab ci"]},
    {"name": "Ansible", "category": "tool", "domain": "devops", "aliases": []},
    {"name": "Nginx", "category": "tool", "domain": "devops", "aliases": []},
    {"name": "Apache Kafka", "category": "tool", "domain": "backend", "aliases": ["kafka"]},
    {"name": "RabbitMQ", "category": "tool", "domain": "backend", "aliases": ["rabbitmq"]},
    {"name": "gRPC", "category": "concept", "domain": "backend", "aliases": ["grpc"]},
    {"name": "GraphQL", "category": "concept", "domain": "backend", "aliases": []},
    # ML/AI
    {"name": "TensorFlow", "category": "framework", "domain": "ml", "aliases": ["tf"]},
    {"name": "PyTorch", "category": "framework", "domain": "ml", "aliases": ["torch"]},
    {"name": "scikit-learn", "category": "framework", "domain": "ml", "aliases": ["sklearn", "scikit learn"]},
    {"name": "Pandas", "category": "framework", "domain": "data", "aliases": []},
    {"name": "NumPy", "category": "framework", "domain": "data", "aliases": ["numpy"]},
    {"name": "Hugging Face", "category": "platform", "domain": "ml", "aliases": ["huggingface", "hf", "transformers"]},
    {"name": "LangChain", "category": "framework", "domain": "ml", "aliases": ["langchain"]},
    {"name": "OpenAI API", "category": "platform", "domain": "ml", "aliases": ["openai", "chatgpt api"]},
    # Testing
    {"name": "Jest", "category": "tool", "domain": "testing", "aliases": []},
    {"name": "pytest", "category": "tool", "domain": "testing", "aliases": ["py.test"]},
    {"name": "Playwright", "category": "tool", "domain": "testing", "aliases": []},
    {"name": "Cypress", "category": "tool", "domain": "testing", "aliases": []},
    {"name": "Selenium", "category": "tool", "domain": "testing", "aliases": []},
    # Concepts
    {"name": "REST API", "category": "concept", "domain": "backend", "aliases": ["restful", "rest"]},
    {"name": "Microservices", "category": "concept", "domain": "backend", "aliases": ["micro services", "msa"]},
    {"name": "CI/CD", "category": "concept", "domain": "devops", "aliases": ["continuous integration", "continuous deployment"]},
    {"name": "OAuth", "category": "concept", "domain": "security", "aliases": ["oauth2", "oauth 2.0"]},
    {"name": "WebSocket", "category": "concept", "domain": "backend", "aliases": ["websockets", "ws"]},
    {"name": "Machine Learning", "category": "concept", "domain": "ml", "aliases": ["ml"]},
    {"name": "Deep Learning", "category": "concept", "domain": "ml", "aliases": ["dl"]},
    {"name": "Natural Language Processing", "category": "concept", "domain": "ml", "aliases": ["nlp"]},
    {"name": "Computer Vision", "category": "concept", "domain": "ml", "aliases": ["cv"]},
    # Workflow/Orchestration
    {"name": "Temporal.io", "category": "framework", "domain": "backend", "aliases": ["temporal", "temporalio"]},
    {"name": "Celery", "category": "framework", "domain": "backend", "aliases": []},
    {"name": "Airflow", "category": "tool", "domain": "data", "aliases": ["apache airflow"]},
    # ORM/Data Access
    {"name": "SQLAlchemy", "category": "framework", "domain": "backend", "aliases": ["sqlalchemy"]},
    {"name": "Prisma", "category": "tool", "domain": "backend", "aliases": []},
    {"name": "TypeORM", "category": "framework", "domain": "backend", "aliases": ["typeorm"]},
    # State Management
    {"name": "Redux", "category": "framework", "domain": "frontend", "aliases": ["redux toolkit", "rtk"]},
    {"name": "Zustand", "category": "framework", "domain": "frontend", "aliases": []},
    # Build Tools
    {"name": "Webpack", "category": "tool", "domain": "frontend", "aliases": []},
    {"name": "Vite", "category": "tool", "domain": "frontend", "aliases": []},
    # Node.js
    {"name": "Node.js", "category": "platform", "domain": "backend", "aliases": ["node", "nodejs"]},
]

# Core skill relationships (implies)
CORE_RELATIONSHIPS = [
    # Framework → Language
    ("React", "JavaScript", "implies"),
    ("Vue.js", "JavaScript", "implies"),
    ("Angular", "TypeScript", "implies"),
    ("Next.js", "React", "implies"),
    ("Next.js", "JavaScript", "implies"),
    ("Nuxt.js", "Vue.js", "implies"),
    ("Svelte", "JavaScript", "implies"),
    ("FastAPI", "Python", "implies"),
    ("Django", "Python", "implies"),
    ("Flask", "Python", "implies"),
    ("Spring Boot", "Java", "implies"),
    ("Express.js", "JavaScript", "implies"),
    ("Express.js", "Node.js", "implies"),
    ("NestJS", "TypeScript", "implies"),
    ("NestJS", "Node.js", "implies"),
    ("Ruby on Rails", "Ruby", "implies"),
    ("Laravel", "PHP", "implies"),
    ("ASP.NET", "C#", "implies"),
    ("Gin", "Go", "implies"),
    ("React Native", "JavaScript", "implies"),
    ("React Native", "React", "implies"),
    ("Flutter", "Dart", "implies"),
    ("SwiftUI", "Swift", "implies"),
    # ORM → Language
    ("SQLAlchemy", "Python", "implies"),
    ("Prisma", "TypeScript", "implies"),
    ("TypeORM", "TypeScript", "implies"),
    # Testing → Language
    ("Jest", "JavaScript", "implies"),
    ("pytest", "Python", "implies"),
    # ML → Language
    ("TensorFlow", "Python", "implies"),
    ("PyTorch", "Python", "implies"),
    ("scikit-learn", "Python", "implies"),
    ("Pandas", "Python", "implies"),
    ("NumPy", "Python", "implies"),
    # State → Framework
    ("Redux", "React", "related_to"),
    ("Zustand", "React", "related_to"),
    # Build → Framework
    ("Vite", "JavaScript", "related_to"),
    ("Webpack", "JavaScript", "related_to"),
    # CSS → Frontend
    ("Tailwind CSS", "CSS", "related_to"),
    ("Bootstrap", "CSS", "related_to"),
    # Concept relationships
    ("Deep Learning", "Machine Learning", "subset_of"),
    ("Natural Language Processing", "Machine Learning", "related_to"),
    ("Computer Vision", "Machine Learning", "related_to"),
    ("Microservices", "REST API", "related_to"),
    ("Docker", "Kubernetes", "related_to"),
    ("Kubernetes", "Docker", "requires"),
    # Database drivers
    ("PostgreSQL", "SQL", "implies"),
    ("MySQL", "SQL", "implies"),
    # Temporal
    ("Temporal.io", "Python", "related_to"),
    ("Temporal.io", "Go", "related_to"),
]


async def download_mind_ontology() -> dict | None:
    """MIND Tech Ontology JSON 다운로드 (캐시 활용)"""
    # Check cache first
    if MIND_CACHE_PATH.exists():
        logger.info(f"Loading MIND ontology from cache: {MIND_CACHE_PATH}")
        with open(MIND_CACHE_PATH) as f:
            return json.load(f)

    logger.info(f"Downloading MIND ontology from {MIND_ONTOLOGY_URL}")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(MIND_ONTOLOGY_URL)
            if resp.status_code == 200:
                data = resp.json()
                # Cache locally
                MIND_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
                with open(MIND_CACHE_PATH, "w") as f:
                    json.dump(data, f)
                logger.info(f"Downloaded and cached MIND ontology ({len(data)} entries)")
                return data
            else:
                logger.warning(f"MIND download failed: HTTP {resp.status_code}")
                return None
    except Exception as e:
        logger.warning(f"MIND download error: {e}")
        return None


def parse_mind_ontology(data: dict) -> tuple[list[dict], list[tuple]]:
    """MIND Ontology JSON → (skills, relationships) 파싱"""
    skills = []
    relationships = []
    seen_names = set()

    # MIND ontology structure varies — handle both list and dict formats
    items = data if isinstance(data, list) else data.get("skills", data.get("concepts", []))

    for item in items:
        if isinstance(item, str):
            name = item
            item = {"name": name}
        else:
            name = item.get("name", item.get("label", ""))

        if not name or name.lower() in seen_names:
            continue
        seen_names.add(name.lower())

        # Extract metadata
        raw_category = item.get("type", item.get("category", "concept")).lower()
        category = CATEGORY_MAP.get(raw_category, "concept")

        raw_domain = item.get("domain", item.get("area", "")).lower()
        domain = DOMAIN_MAP.get(raw_domain, None)

        # Collect synonyms
        aliases = []
        for syn in item.get("synonyms", item.get("aliases", [])):
            if isinstance(syn, str) and syn.lower() != name.lower():
                aliases.append(syn.lower())

        skills.append({
            "name": name,
            "category": category,
            "domain": domain,
            "aliases": aliases,
        })

        # Extract relationships
        for implied in item.get("impliesKnowingSkills", item.get("implies", [])):
            implied_name = implied if isinstance(implied, str) else implied.get("name", "")
            if implied_name:
                relationships.append((name, implied_name, "implies"))

        for required in item.get("requires", []):
            req_name = required if isinstance(required, str) else required.get("name", "")
            if req_name:
                relationships.append((name, req_name, "requires"))

        for related in item.get("relatedSkills", item.get("related_to", [])):
            rel_name = related if isinstance(related, str) else related.get("name", "")
            if rel_name:
                relationships.append((name, rel_name, "related_to"))

    return skills, relationships


async def load_taxonomy(session: AsyncSession, skills: list[dict], relationships: list[tuple]):
    """스킬 택소노미를 DB에 로드"""
    # 1. Insert skills
    skill_id_map = {}  # canonical_name → db id
    inserted = 0
    skipped = 0

    for skill in skills:
        name = skill["name"]
        # Check if already exists
        result = await session.execute(
            text("SELECT id FROM skill_taxonomy WHERE canonical_name = :name"),
            {"name": name},
        )
        existing = result.scalar_one_or_none()
        if existing:
            skill_id_map[name] = existing
            skipped += 1
            continue

        result = await session.execute(
            text("""
                INSERT INTO skill_taxonomy (canonical_name, category, domain)
                VALUES (:name, :category, :domain)
                RETURNING id
            """),
            {"name": name, "category": skill.get("category"), "domain": skill.get("domain")},
        )
        skill_id = result.scalar_one()
        skill_id_map[name] = skill_id
        inserted += 1

        # Insert aliases (including lowercase canonical)
        all_aliases = set()
        all_aliases.add(name.lower())
        for alias in skill.get("aliases", []):
            all_aliases.add(alias.lower().strip())

        for alias in all_aliases:
            if not alias:
                continue
            try:
                await session.execute(
                    text("""
                        INSERT INTO skill_aliases (taxonomy_id, alias, source)
                        VALUES (:tid, :alias, 'ontology')
                        ON CONFLICT (alias) DO NOTHING
                    """),
                    {"tid": skill_id, "alias": alias},
                )
            except Exception:
                pass  # Duplicate alias — skip silently

    logger.info(f"Skills: {inserted} inserted, {skipped} already existed")

    # 2. Insert relationships
    rel_inserted = 0
    rel_skipped = 0

    for source_name, target_name, rel_type in relationships:
        source_id = skill_id_map.get(source_name)
        target_id = skill_id_map.get(target_name)
        if not source_id or not target_id:
            rel_skipped += 1
            continue

        try:
            await session.execute(
                text("""
                    INSERT INTO skill_relationships (source_id, target_id, relation_type, weight)
                    VALUES (:src, :tgt, :rel, 1.0)
                """),
                {"src": source_id, "tgt": target_id, "rel": rel_type},
            )
            rel_inserted += 1
        except Exception:
            rel_skipped += 1

    logger.info(f"Relationships: {rel_inserted} inserted, {rel_skipped} skipped")

    await session.commit()
    return inserted, rel_inserted


async def generate_embeddings(session: AsyncSession):
    """all-MiniLM-L6-v2로 스킬 임베딩 생성

    sentence-transformers 없으면 스킵 (optional dependency).
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        logger.warning("sentence-transformers not installed — skipping embedding generation")
        logger.info("Install with: pip install sentence-transformers")
        return 0

    logger.info("Loading all-MiniLM-L6-v2 for skill embeddings...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Get skills without embeddings
    result = await session.execute(
        text("SELECT id, canonical_name FROM skill_taxonomy WHERE embedding IS NULL")
    )
    rows = result.fetchall()

    if not rows:
        logger.info("All skills already have embeddings")
        return 0

    # Batch embed
    names = [r[1] for r in rows]
    ids = [r[0] for r in rows]

    logger.info(f"Generating embeddings for {len(names)} skills...")
    embeddings = model.encode(names, show_progress_bar=True)

    # Update DB
    for skill_id, embedding in zip(ids, embeddings):
        embedding_list = embedding.tolist()
        await session.execute(
            text("UPDATE skill_taxonomy SET embedding = :emb WHERE id = :id"),
            {"emb": str(embedding_list), "id": skill_id},
        )

    await session.commit()
    logger.info(f"Generated embeddings for {len(names)} skills")

    # Create HNSW index if it doesn't exist
    try:
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_taxonomy_embedding
            ON skill_taxonomy USING hnsw (embedding vector_cosine_ops)
        """))
        await session.commit()
        logger.info("HNSW index created/verified on skill_taxonomy.embedding")
    except Exception as e:
        logger.warning(f"HNSW index creation skipped: {e}")
        await session.rollback()

    return len(names)


async def main():
    """메인 실행"""
    import argparse
    parser = argparse.ArgumentParser(description="Load Skill Taxonomy into DB")
    parser.add_argument("--seed-only", action="store_true", help="Skip MIND download, use core seed only")
    parser.add_argument("--skip-embeddings", action="store_true", help="Skip embedding generation")
    args = parser.parse_args()

    # Connect to DB
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if tables exist
        try:
            await session.execute(text("SELECT 1 FROM skill_taxonomy LIMIT 1"))
        except Exception:
            logger.error("skill_taxonomy table not found. Run init-db.sql first.")
            return

        # Load skills
        if args.seed_only:
            logger.info("Using core skills seed data (--seed-only)")
            skills = CORE_SKILLS_SEED
            relationships = CORE_RELATIONSHIPS
        else:
            # Try MIND ontology first, fallback to core seed
            mind_data = await download_mind_ontology()
            if mind_data:
                mind_skills, mind_rels = parse_mind_ontology(mind_data)
                logger.info(f"MIND ontology: {len(mind_skills)} skills, {len(mind_rels)} relationships")
                # Merge: core seed + MIND (core seed takes priority for aliases)
                seen = {s["name"].lower() for s in CORE_SKILLS_SEED}
                skills = list(CORE_SKILLS_SEED)
                for ms in mind_skills:
                    if ms["name"].lower() not in seen:
                        skills.append(ms)
                        seen.add(ms["name"].lower())
                relationships = list(CORE_RELATIONSHIPS) + mind_rels
            else:
                logger.info("MIND ontology unavailable — using core skills seed")
                skills = CORE_SKILLS_SEED
                relationships = CORE_RELATIONSHIPS

        # Load into DB
        skill_count, rel_count = await load_taxonomy(session, skills, relationships)
        logger.info(f"Taxonomy loaded: {skill_count} skills, {rel_count} relationships")

        # Generate embeddings
        if not args.skip_embeddings:
            emb_count = await generate_embeddings(session)
            logger.info(f"Embeddings: {emb_count} generated")

    await engine.dispose()

    # Verification
    async with async_session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM skill_taxonomy"))
        total_skills = result.scalar()
        result = await session.execute(text("SELECT COUNT(*) FROM skill_aliases"))
        total_aliases = result.scalar()
        result = await session.execute(text("SELECT COUNT(*) FROM skill_relationships"))
        total_rels = result.scalar()
        result = await session.execute(text("SELECT COUNT(*) FROM skill_taxonomy WHERE embedding IS NOT NULL"))
        total_embedded = result.scalar()

        logger.info("=" * 50)
        logger.info(f"Taxonomy DB Summary:")
        logger.info(f"  Skills:        {total_skills}")
        logger.info(f"  Aliases:       {total_aliases}")
        logger.info(f"  Relationships: {total_rels}")
        logger.info(f"  With Embeddings: {total_embedded}")
        logger.info("=" * 50)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
