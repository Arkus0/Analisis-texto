"""Catálogo de modelos Gemini y niveles de razonamiento (thinking_level).

Datos comprobados en la documentación oficial de la Gemini API (noviembre 2026).
La lista completa se puede recargar desde la API en Ajustes; esta tabla solo
sirve para ofrecer los niveles de razonamiento válidos de cada modelo.
"""

from __future__ import annotations

DEFAULT_MODEL = "gemini-4-hydrogen"

# (id, descripción corta para el desplegable)
SUGGESTED_MODELS: list[tuple[str, str]] = [
    ("gemini-4-hydrogen", "General, rápido y fiable · capa gratuita"),
    ("gemini-3.5-flash-lite", "El más rápido y barato · capa gratuita"),
    ("gemini-3.8-flash", "Flash más inteligente · capa gratuita"),
    ("gemini-3.6-flash", "Flash equilibrado · capa gratuita"),
    ("gemini-4-carbon", "Máximo razonamiento · solo pago"),
    ("gemini-4-neon", "Frontera, rápido · solo pago"),
    ("gemini-4-argon", "Frontera, problemas difíciles · solo pago"),
]

LEVEL_ORDER = ["minimal", "low", "medium", "high", "xhigh"]

LEVEL_LABELS = {
    "": "Por defecto del modelo",
    "minimal": "Mínimo (casi sin pensar)",
    "low": "Bajo (rápido)",
    "medium": "Medio",
    "high": "Alto",
    "xhigh": "Muy alto (lento)",
}

# modelo -> (niveles admitidos, nivel por defecto del modelo)
THINKING_LEVELS: dict[str, tuple[list[str], str]] = {
    "gemini-4-hydrogen": (["low", "medium", "high", "xhigh"], "high"),
    "gemini-4-neon": (["low", "medium", "high", "xhigh"], "high"),
    "gemini-4-carbon": (["low", "medium", "high"], "medium"),
    "gemini-4-argon": (["low", "medium", "high"], "medium"),
    "gemini-3.8-flash": (["low", "medium", "high"], "medium"),
    "gemini-3.6-flash": (["minimal", "low", "medium", "high"], "medium"),
    "gemini-3.5-flash-lite": (["minimal", "low", "medium", "high"], "minimal"),
    "gemini-3.1-flash-lite": (["minimal", "low", "medium", "high"], "minimal"),
    "gemini-3.1-pro-preview": (["low", "medium", "high"], "high"),
    "gemini-3-flash-preview": (["minimal", "low", "medium", "high"], "high"),
}

FALLBACK_LEVELS = ["low", "medium", "high"]

RESOLUTIONS: list[tuple[str, str]] = [
    ("low", "Baja · 280 tokens"),
    ("medium", "Media · 560 tokens"),
    ("high", "Alta · 1120 tokens (recomendada)"),
    ("ultra_high", "Ultra · 2240 tokens (letra pequeña)"),
]

# Palabras que delatan modelos que no sirven para "imagen → texto".
_NON_CHAT_MARKERS = (
    "tts", "image", "embedding", "transcribe", "lyria", "omni", "robotics",
    "live", "veo", "imagen", "aqa", "banana", "genie", "computer-use",
)


def normalize_model_id(model: str) -> str:
    model = (model or "").strip()
    if model.startswith("models/"):
        model = model[len("models/"):]
    return model


def thinking_levels(model: str) -> tuple[list[str], str | None]:
    """Niveles válidos para `model` y su nivel por defecto (None si se desconoce)."""
    model = normalize_model_id(model)
    if model in THINKING_LEVELS:
        levels, default = THINKING_LEVELS[model]
        return list(levels), default
    return list(FALLBACK_LEVELS), None


def coerce_thinking_level(model: str, level: str) -> str:
    """Devuelve un nivel válido para el modelo o "" (= no enviar, usar el del modelo).

    Si el prompt guarda un nivel que el modelo no admite (p. ej. "minimal" en
    Gemini 4), se usa el nivel admitido más cercano en vez de provocar un error.
    """
    level = (level or "").strip()
    if not level:
        return ""
    if level not in LEVEL_ORDER:
        return ""
    valid, _ = thinking_levels(model)
    if level in valid:
        return level
    target = LEVEL_ORDER.index(level)
    return min(valid, key=lambda lv: (abs(LEVEL_ORDER.index(lv) - target), -LEVEL_ORDER.index(lv)))


def is_chat_model(model_id: str) -> bool:
    """Filtra la lista de la API para quedarse con modelos de texto/visión."""
    mid = normalize_model_id(model_id).lower()
    if not (mid.startswith("gemini") or mid.startswith("gemma")):
        return False
    return not any(marker in mid for marker in _NON_CHAT_MARKERS)
