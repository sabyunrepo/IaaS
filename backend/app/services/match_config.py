"""Shared color/icon configuration for match levels and valid UI colors."""

# Match level → (color, icon) mapping used by competency matching
MATCH_LEVEL_CONFIG: dict[str, tuple[str, str]] = {
    "strong": ("emerald", "✅"),
    "match": ("emerald", "✅"),
    "partial": ("amber", "⚠️"),
    "unknown": ("amber", "⚠️"),
    "none": ("red", "❌"),
}

MATCH_LEVEL_DEFAULT: tuple[str, str] = ("slate", "❓")

# Valid Tailwind color tokens for LLM-generated UI elements
VALID_COLORS: frozenset[str] = frozenset({"emerald", "blue", "amber", "red", "slate"})

DEFAULT_COLOR: str = "slate"


def get_match_color_icon(match_level: str) -> tuple[str, str]:
    """Return (color, icon) for a given match level."""
    return MATCH_LEVEL_CONFIG.get(match_level, MATCH_LEVEL_DEFAULT)


def sanitize_color(color: str) -> str:
    """Return color if valid, else default."""
    return color if color in VALID_COLORS else DEFAULT_COLOR
