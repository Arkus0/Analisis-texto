"""Llamadas a Gemini con la Interactions API (google-genai >= 2.3), en streaming.

Cada captura es una interacción independiente y se envía con store=False, así
Google no guarda la petición para recuperarla después.
"""

from __future__ import annotations

import base64
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator

from .config import Preset, Settings
from .models import coerce_thinking_level, is_chat_model, normalize_model_id

REQUEST_TIMEOUT_S = 120.0


class GeminiError(Exception):
    pass


@dataclass
class Citation:
    url: str
    title: str = ""


@dataclass
class StreamPiece:
    """Un trozo de la respuesta: texto o citas de la búsqueda en Google."""

    text: str = ""
    citations: list[Citation] = field(default_factory=list)


def build_request(preset: Preset, settings: Settings, image_bytes: bytes,
                  mime_type: str = "image/jpeg") -> dict[str, Any]:
    model = normalize_model_id(settings.model_for(preset))
    image: dict[str, Any] = {
        "type": "image",
        "data": base64.b64encode(image_bytes).decode("ascii"),
        "mime_type": mime_type,
    }
    if preset.resolution:
        image["resolution"] = preset.resolution

    request: dict[str, Any] = {
        "model": model,
        "input": [
            image,
            {"type": "text", "text": (preset.prompt or "").strip() or "Analiza la captura."},
        ],
        "store": False,
        "stream": True,
    }
    if (preset.system_instruction or "").strip():
        request["system_instruction"] = preset.system_instruction.strip()

    generation: dict[str, Any] = {}
    level = coerce_thinking_level(model, preset.thinking_level)
    if level:
        generation["thinking_level"] = level
    if preset.max_output_tokens and preset.max_output_tokens > 0:
        generation["max_output_tokens"] = int(preset.max_output_tokens)
    if generation:
        request["generation_config"] = generation

    if preset.google_search:
        request["tools"] = [{"type": "google_search"}]
    return request


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _citations(annotations: Iterable[Any] | None) -> list[Citation]:
    out: list[Citation] = []
    for a in annotations or []:
        if _get(a, "type") == "url_citation" and _get(a, "url"):
            out.append(Citation(url=_get(a, "url"), title=_get(a, "title") or ""))
    return out


def iter_pieces(events: Iterable[Any]) -> Iterator[StreamPiece]:
    """Convierte los eventos SSE de la Interactions API en trozos de texto/citas."""
    for ev in events:
        etype = _get(ev, "event_type")
        if etype == "step.delta":
            delta = _get(ev, "delta")
            dtype = _get(delta, "type")
            if dtype == "text":
                text = _get(delta, "text") or ""
                if text:
                    yield StreamPiece(text=text)
            elif dtype == "text_annotation_delta":
                cites = _citations(_get(delta, "annotations"))
                if cites:
                    yield StreamPiece(citations=cites)
        elif etype == "step.start":
            step = _get(ev, "step")
            if _get(step, "type") == "model_output":
                for content in _get(step, "content") or []:
                    if _get(content, "type") == "text" and _get(content, "text"):
                        yield StreamPiece(text=_get(content, "text"),
                                          citations=_citations(_get(content, "annotations")))
        elif etype == "error":
            err = _get(ev, "error")
            msg = _get(err, "message") or _get(err, "code") or "error desconocido"
            raise GeminiError(str(msg))


def friendly_error(exc: BaseException) -> str:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    text = str(exc).strip() or exc.__class__.__name__
    if status in (401, 403):
        return f"API key no válida o sin permiso ({status}). Revísala en Ajustes."
    if status == 404:
        return f"Modelo no encontrado (404). Elige otro en Ajustes.\n{text[:300]}"
    if status == 429:
        return "Cuota o límite de velocidad agotado (429). Espera un poco o cambia de modelo."
    if status == 400:
        return f"Petición rechazada (400). Revisa el modelo, el razonamiento o la resolución.\n{text[:300]}"
    name = exc.__class__.__name__
    if "Timeout" in name:
        return "Gemini ha tardado demasiado en responder (timeout)."
    if "Connection" in name:
        return "Sin conexión con Gemini. Comprueba tu conexión a internet."
    return text[:400]


ClientFactory = Callable[[str], Any]


def _default_client_factory(api_key: str) -> Any:
    from google import genai

    return genai.Client(api_key=api_key)


class GeminiService:
    """Lanza cada petición en un hilo y avisa mediante callbacks (desde ese hilo)."""

    def __init__(self, client_factory: ClientFactory = _default_client_factory):
        self._client_factory = client_factory
        self._client = None
        self._client_key = None
        self._lock = threading.Lock()

    def _client_for(self, api_key: str):
        with self._lock:
            if self._client is None or self._client_key != api_key:
                self._client = self._client_factory(api_key)
                self._client_key = api_key
            return self._client

    def stream(self, api_key: str, request: dict[str, Any]) -> Iterator[StreamPiece]:
        client = self._client_for(api_key)
        events = client.interactions.create(timeout=REQUEST_TIMEOUT_S, **request)
        yield from iter_pieces(events)

    def start(
        self,
        api_key: str,
        request: dict[str, Any],
        on_piece: Callable[[StreamPiece], None],
        on_done: Callable[[], None],
        on_error: Callable[[str], None],
    ) -> threading.Thread:
        def run():
            try:
                for piece in self.stream(api_key, request):
                    on_piece(piece)
            except GeminiError as e:
                on_error(str(e))
            except Exception as e:  # noqa: BLE001 - cualquier fallo se muestra en la franja
                on_error(friendly_error(e))
            else:
                on_done()

        t = threading.Thread(target=run, name="gemini-request", daemon=True)
        t.start()
        return t

    def list_models(self, api_key: str) -> list[str]:
        client = self._client_for(api_key)
        ids: list[str] = []
        for m in client.models.list():
            mid = normalize_model_id(getattr(m, "name", "") or "")
            actions = getattr(m, "supported_actions", None) or []
            if actions and "generateContent" not in actions:
                continue
            if mid and is_chat_model(mid):
                ids.append(mid)
        return sorted(set(ids), reverse=True)
