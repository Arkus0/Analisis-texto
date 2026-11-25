"""Configuración persistente (JSON) y API key (Administrador de credenciales)."""

from __future__ import annotations

import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from .models import DEFAULT_MODEL

APP_NAME = "OverlayGemini"
KEYRING_SERVICE = APP_NAME
KEYRING_USER = "gemini_api_key"
ENV_API_KEY = "GEMINI_API_KEY"


def config_dir() -> Path:
    override = os.environ.get("OVERLAY_GEMINI_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home())
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return base / APP_NAME


def config_path() -> Path:
    return config_dir() / "config.json"


# --------------------------------------------------------------------------- modelos


@dataclass
class Binding:
    """Un botón físico. kind: gamepad | joystick | mouse | keyboard."""

    kind: str
    code: str
    label: str = ""

    def describe(self) -> str:
        return self.label or f"{self.kind}:{self.code}"


@dataclass
class Preset:
    id: str
    name: str
    system_instruction: str
    prompt: str
    model: str = ""  # vacío = modelo global
    thinking_level: str = "low"  # "" = el del modelo
    resolution: str = "high"
    google_search: bool = False
    max_output_tokens: int = 0  # 0 = sin límite


@dataclass
class OverlayStyle:
    vertical_center: float = 0.50  # centro de la franja, fracción del alto del monitor
    max_width: float = 0.70  # ancho máximo normal, fracción del monitor
    wide_width: float = 0.95  # ancho al que se ensancha si no cabe
    max_height: float = 0.45  # alto máximo, fracción del monitor
    min_width_px: int = 360
    opacity: float = 0.90
    font_px: int = 21
    min_font_ratio: float = 0.70
    fade_ms: int = 220  # duración de los fundidos (0 = sin animación)


@dataclass
class Settings:
    model: str = DEFAULT_MODEL
    active_preset_id: str = ""
    presets: list[Preset] = field(default_factory=list)
    capture_binding: Binding | None = None
    screen_name: str = ""  # vacío = pantalla principal
    capture_region: list[float] | None = None  # [x, y, w, h] en fracciones; None = pantalla completa
    max_image_width: int = 1920  # 0 = resolución original
    long_press_ms: int = 600
    wait_timeout_s: int = 40  # pasado este tiempo, el icono se pone rojo
    exclude_from_capture: bool = True
    overlay: OverlayStyle = field(default_factory=OverlayStyle)

    def active_preset(self) -> Preset:
        for p in self.presets:
            if p.id == self.active_preset_id:
                return p
        if not self.presets:
            self.presets = default_presets()
        self.active_preset_id = self.presets[0].id
        return self.presets[0]

    def model_for(self, preset: Preset) -> str:
        return (preset.model or "").strip() or self.model or DEFAULT_MODEL


# --------------------------------------------------------------------------- defaults

_BREVITY = (
    "Responde SIEMPRE en español de España. Ve directo al grano: sin saludos, sin "
    "preámbulos, sin repetir la pregunta y sin frases de cierre. Máximo 6-8 líneas "
    "cortas; usa viñetas solo si aportan claridad y **negrita** para el término clave. "
    "La respuesta se lee de un vistazo en una franja sobre un vídeo: cada palabra cuenta."
)


def new_id() -> str:
    return uuid.uuid4().hex[:10]


def default_presets() -> list[Preset]:
    return [
        Preset(
            id="dudas",
            name="Dudas",
            system_instruction=(
                "Eres un tutor experto en Seguridad Social y legislación laboral española. "
                "Recibes una captura de pantalla de un curso. " + _BREVITY
            ),
            prompt=(
                "Explica lo esencial de lo que aparece en pantalla y aclara cualquier "
                "concepto que pueda generar dudas."
            ),
        ),
        Preset(
            id="definicion",
            name="Definición exacta",
            system_instruction=(
                "Eres un jurista especializado en Seguridad Social española. Das "
                "definiciones exactas y literales; si existe definición legal, cita la "
                "norma y el artículo (p. ej. LGSS, RD). Si no estás seguro, dilo: nunca "
                "inventes artículos ni cifras. " + _BREVITY
            ),
            prompt=(
                "Da la definición exacta del término o concepto principal que aparece en "
                "pantalla, con su fuente normativa si la tiene."
            ),
            google_search=True,
        ),
        Preset(
            id="traduccion",
            name="Traducción",
            system_instruction=(
                "Eres un traductor profesional al español de España. Traduces con "
                "fidelidad, manteniendo la terminología técnica. Devuelve solo la "
                "traducción, sin comentarios. Si el texto es largo, traduce lo principal "
                "en un máximo de 8 líneas."
            ),
            prompt="Traduce al español el texto visible en la captura.",
            thinking_level="low",
        ),
    ]


def default_settings() -> Settings:
    presets = default_presets()
    return Settings(presets=presets, active_preset_id=presets[0].id)


# --------------------------------------------------------------------------- (de)serialización


def _from_dict(cls, data: Any):
    """Crea un dataclass ignorando claves desconocidas y usando defaults si faltan."""
    if not isinstance(data, dict):
        return cls() if cls is not Preset and cls is not Binding else None
    known = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in data.items() if k in known})


def settings_to_dict(s: Settings) -> dict:
    return asdict(s)


def settings_from_dict(data: dict) -> Settings:
    base = default_settings()
    if not isinstance(data, dict):
        return base
    s = Settings()
    for f in fields(Settings):
        if f.name in ("presets", "capture_binding", "overlay"):
            continue
        setattr(s, f.name, data.get(f.name, getattr(base, f.name)))

    presets: list[Preset] = []
    for raw in data.get("presets") or []:
        if isinstance(raw, dict) and raw.get("id") and raw.get("name") is not None:
            try:
                presets.append(_from_dict(Preset, {
                    "system_instruction": "", "prompt": "", **raw,
                }))
            except TypeError:
                continue
    s.presets = presets or base.presets

    raw_binding = data.get("capture_binding")
    if isinstance(raw_binding, dict) and raw_binding.get("kind") and raw_binding.get("code"):
        s.capture_binding = _from_dict(Binding, raw_binding)

    s.overlay = _from_dict(OverlayStyle, data.get("overlay") or {})
    s.capture_region = normalize_region(data.get("capture_region"))
    s.active_preset()  # repara active_preset_id si no existe
    return s


def normalize_region(region: Any) -> list[float] | None:
    """Valida una zona [x, y, w, h] (fracciones 0..1). Devuelve None si no sirve."""
    try:
        x, y, w, h = (float(v) for v in region)
    except (TypeError, ValueError):
        return None
    x, y = min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0)
    w, h = min(w, 1.0 - x), min(h, 1.0 - y)
    if w < 0.02 or h < 0.02:
        return None
    if x == 0.0 and y == 0.0 and w >= 0.999 and h >= 0.999:
        return None  # es la pantalla completa
    return [round(x, 5), round(y, 5), round(w, 5), round(h, 5)]


def load_settings(path: Path | None = None) -> Settings:
    path = path or config_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default_settings()
    except (OSError, ValueError):
        # Config corrupta: se guarda una copia y se arranca con valores por defecto.
        try:
            path.replace(path.with_suffix(".corrupt.json"))
        except OSError:
            pass
        return default_settings()
    return settings_from_dict(data)


def save_settings(settings: Settings, path: Path | None = None) -> None:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(settings_to_dict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# --------------------------------------------------------------------------- API key


def api_key_from_env() -> str:
    return (os.environ.get(ENV_API_KEY) or os.environ.get("GOOGLE_API_KEY") or "").strip()


def get_api_key() -> str:
    env = api_key_from_env()
    if env:
        return env
    try:
        import keyring

        return (keyring.get_password(KEYRING_SERVICE, KEYRING_USER) or "").strip()
    except Exception:
        return ""


def set_api_key(key: str) -> None:
    """Guarda la key en el Administrador de credenciales de Windows (keyring)."""
    import keyring

    key = (key or "").strip()
    if key:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key)
    else:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
        except Exception:
            pass
