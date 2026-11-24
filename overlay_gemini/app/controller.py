"""Lógica del botón: captura → Gemini → mostrar / ocultar, con pulsación larga.

Pulsación corta con la franja oculta  → nueva captura y pregunta.
Pulsación corta con la franja visible → ocultar.
Pulsación larga (≥ long_press_ms)     → volver a mostrar la última respuesta.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from .config import Settings, get_api_key
from .gemini_client import GeminiService, StreamPiece, build_request

DEBOUNCE_S = 0.25


class OverlayLike(Protocol):
    def is_shown(self) -> bool: ...
    def has_content(self) -> bool: ...
    def begin(self, header: str) -> None: ...
    def set_header(self, header: str) -> None: ...
    def set_body(self, markdown: str) -> None: ...
    def add_citations(self, citations) -> None: ...
    def finish(self, header: str) -> None: ...
    def show_message(self, header: str, message: str, error: bool = False, show: bool = True) -> None: ...
    def show_overlay(self) -> None: ...
    def hide_overlay(self) -> None: ...


def _fmt_seconds(s: float) -> str:
    return f"{s:.1f} s".replace(".", ",")


class Controller(QObject):
    # Señales para pasar del hilo de Gemini al hilo de la interfaz.
    _piece = Signal(int, object)
    _done = Signal(int)
    _failed = Signal(int, str)

    status_changed = Signal(str)

    def __init__(
        self,
        overlay: OverlayLike,
        settings_provider: Callable[[], Settings],
        capture: Callable[[Settings], bytes],
        gemini: GeminiService,
        api_key_provider: Callable[[], str] = get_api_key,
        clock: Callable[[], float] = time.monotonic,
    ):
        super().__init__()
        self.overlay = overlay
        self._settings = settings_provider
        self._capture = capture
        self._gemini = gemini
        self._api_key = api_key_provider
        self._clock = clock

        self._down_at: float | None = None
        self._last_action = -1e9
        self._rid = 0
        self._text = ""
        self._started = 0.0
        self._header_base = ""

        self._piece.connect(self._on_piece)
        self._done.connect(self._on_done)
        self._failed.connect(self._on_failed)

    # ----------------------------------------------------------------- botón
    @Slot()
    def press(self) -> None:
        if self._down_at is None:  # ignora auto-repetición del teclado
            self._down_at = self._clock()

    @Slot()
    def release(self) -> None:
        if self._down_at is None:
            return
        now = self._clock()
        held = now - self._down_at
        self._down_at = None
        if now - self._last_action < DEBOUNCE_S:
            return
        self._last_action = now
        if held * 1000 >= self._settings().long_press_ms:
            self.show_last()
        elif self.overlay.is_shown():
            self.overlay.hide_overlay()
        else:
            self.capture_and_ask()

    # ----------------------------------------------------------------- acciones
    def show_last(self) -> None:
        if self.overlay.has_content():
            self.overlay.show_overlay()
        else:
            self.overlay.show_message("Overlay Gemini", "Aún no hay ninguna respuesta.")

    def capture_and_ask(self) -> None:
        settings = self._settings()
        preset = settings.active_preset()
        model = settings.model_for(preset)
        self._rid += 1
        rid = self._rid
        self._text = ""
        self._header_base = f"{preset.name} · {model}"

        key = self._api_key()
        if not key:
            self.overlay.show_message(
                "Falta la API key", "Abre **Ajustes** (icono de la bandeja) y pega tu API key de Gemini.",
                error=True)
            return
        try:
            image = self._capture(settings)
        except Exception as e:  # noqa: BLE001
            self.overlay.show_message("Error de captura", str(e), error=True)
            return

        self._started = self._clock()
        self.overlay.begin(self._header_base)
        self.status_changed.emit("analizando")
        request = build_request(preset, settings, image)
        self._gemini.start(
            key,
            request,
            on_piece=lambda piece: self._piece.emit(rid, piece),
            on_done=lambda: self._done.emit(rid),
            on_error=lambda msg: self._failed.emit(rid, msg),
        )

    # ----------------------------------------------------------------- respuestas
    def _elapsed(self) -> str:
        return _fmt_seconds(self._clock() - self._started)

    @Slot(int, object)
    def _on_piece(self, rid: int, piece: StreamPiece) -> None:
        if rid != self._rid:
            return  # respuesta de una captura anterior
        if piece.text:
            self._text += piece.text
            self.overlay.set_body(self._text)
        if piece.citations:
            self.overlay.add_citations(piece.citations)

    @Slot(int)
    def _on_done(self, rid: int) -> None:
        if rid != self._rid:
            return
        self.overlay.finish(f"{self._header_base} · {self._elapsed()}")
        self.status_changed.emit("listo")

    @Slot(int, str)
    def _on_failed(self, rid: int, message: str) -> None:
        if rid != self._rid:
            return
        # Si el usuario ya había ocultado la franja, no se la volvemos a poner delante:
        # el error queda guardado y se ve con una pulsación larga.
        self.overlay.show_message(f"Error · {self._header_base}", message, error=True,
                                  show=self.overlay.is_shown())
        self.status_changed.emit("error")
