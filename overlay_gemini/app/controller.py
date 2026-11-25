"""Lógica del botón con tres estados: IDLE → WAITING → SHOWING.

Pulsación corta en IDLE     → captura, icono de espera, petición en segundo plano.
Respuesta lista en WAITING  → el icono se desvanece y entra la franja.
Pulsación corta en WAITING  → cancela la espera; la respuesta se guarda en silencio
                              y NUNCA aparece sola después.
Pulsación corta en SHOWING  → la franja se desvanece.
Error / tiempo agotado      → solo el icono se pone rojo 2 s (si estaba visible).
Pulsación larga             → última respuesta (o error); si aún está pendiente,
                              vuelve a mostrar el icono de espera.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from PySide6.QtCore import QObject, QTimer, Signal, Slot

from .config import Settings, get_api_key
from .gemini_client import Citation, StreamPiece, Timing, build_request

log = logging.getLogger("overlay_gemini")

DEBOUNCE_S = 0.25
ERROR_HOLD_MS = 2000

IDLE, WAITING, SHOWING = "idle", "waiting", "showing"


class BandLike(Protocol):
    def is_shown(self) -> bool: ...
    def has_content(self) -> bool: ...
    def show_answer(self, header: str, markdown: str, citations=None, error: bool = False) -> None: ...
    def fade_out(self, ms: int | None = None) -> None: ...
    def hide_now(self) -> None: ...


class IconLike(Protocol):
    def start(self) -> None: ...
    def flash_error(self, hold_ms: int = ERROR_HOLD_MS) -> None: ...
    def fade_out(self, ms: int | None = None) -> None: ...
    def hide_now(self) -> None: ...
    def is_shown(self) -> bool: ...


@dataclass
class Result:
    header: str
    text: str
    error: bool = False
    citations: list[Citation] = field(default_factory=list)


def _fmt_seconds(s: float) -> str:
    return f"{s:.1f} s".replace(".", ",")


class Controller(QObject):
    # Del hilo de Gemini al hilo de la interfaz.
    _piece = Signal(int, object)
    _done = Signal(int, object)
    _failed = Signal(int, str)

    state_changed = Signal(str)

    def __init__(
        self,
        band: BandLike,
        icon: IconLike,
        settings_provider: Callable[[], Settings],
        grab: Callable[[Settings], Any],
        prepare: Callable[[Any, Settings], bytes],
        gemini,
        api_key_provider: Callable[[], str] = get_api_key,
        clock: Callable[[], float] = time.monotonic,
    ):
        super().__init__()
        self.band = band
        self.icon = icon
        self._settings = settings_provider
        self._grab = grab
        self._prepare = prepare
        self._gemini = gemini
        self._api_key = api_key_provider
        self._clock = clock

        self.state = IDLE
        self._down_at: float | None = None
        self._last_action = -1e9
        self._rid = 0
        self._pending = False
        self._text = ""
        self._citations: list[Citation] = []
        self._header_base = ""
        self._started = 0.0
        self.last: Result | None = None

        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._on_timeout)

        self._piece.connect(self._on_piece)
        self._done.connect(self._on_done)
        self._failed.connect(self._on_failed)

    # ----------------------------------------------------------------- backend (prueba de impacto)
    def set_backend(self, gemini, api_key_provider: Callable[[], str]) -> None:
        self._gemini = gemini
        self._api_key = api_key_provider

    @property
    def backend(self):
        return self._gemini, self._api_key

    def _set_state(self, state: str) -> None:
        if state != self.state:
            self.state = state
            self.state_changed.emit(state)

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
        else:
            self.toggle()

    def toggle(self) -> None:
        """Lo que hace una pulsación corta."""
        if self.state == WAITING:
            self.cancel_wait()
        elif self.state == SHOWING:
            self.hide_answer()
        else:
            self.capture_and_ask()

    # ----------------------------------------------------------------- acciones
    def reset(self) -> None:
        """Lo oculta todo al instante y descarta lo pendiente (fin de la prueba de impacto)."""
        self._rid += 1
        self._pending = False
        self._timeout.stop()
        self.icon.hide_now()
        self.band.hide_now()
        self._set_state(IDLE)

    def cancel_wait(self) -> None:
        self.icon.fade_out()
        self._set_state(IDLE)

    def hide_answer(self) -> None:
        self.band.fade_out()
        self._set_state(IDLE)

    def show_last(self) -> None:
        if self._pending:
            self.band.hide_now()
            self.icon.start()
            self._set_state(WAITING)
        elif self.last is not None:
            self.icon.hide_now()
            self.band.show_answer(self.last.header, self.last.text, self.last.citations, self.last.error)
            self._set_state(SHOWING)
        # Sin nada que mostrar: no se hace nada (nada de avisos).

    def capture_and_ask(self) -> None:
        settings = self._settings()
        preset = settings.active_preset()
        model = settings.model_for(preset)
        self._rid += 1
        rid = self._rid
        self._text = ""
        self._citations = []
        self._header_base = f"{preset.name} · {model}"

        # Lo que quede en pantalla (p. ej. un fundido de salida) se quita antes de capturar.
        self.band.hide_now()
        self.icon.hide_now()

        key = self._api_key()
        if not key:
            self._store_error("Falta la API key: abre Ajustes (icono de la bandeja) y pégala.")
            self.icon.flash_error(ERROR_HOLD_MS)
            return
        try:
            t0 = time.perf_counter()
            image = self._grab(settings)
            grab_ms = (time.perf_counter() - t0) * 1000
        except Exception as e:  # noqa: BLE001
            log.warning("Fallo de captura: %s", e)
            self._store_error(f"Error de captura: {e}")
            self.icon.flash_error(ERROR_HOLD_MS)
            return

        self._pending = True
        self._started = self._clock()
        self.icon.start()
        self._set_state(WAITING)
        self._timeout.start(max(5, int(settings.wait_timeout_s)) * 1000)
        log.info("Captura %.0f ms · %s", grab_ms, self._header_base)

        prepare = self._prepare

        def make_request():  # se ejecuta en el hilo de la petición
            return build_request(preset, settings, prepare(image, settings))

        self._gemini.start(
            key,
            make_request,
            on_piece=lambda piece: self._piece.emit(rid, piece),
            on_done=lambda timing=None: self._done.emit(rid, timing),
            on_error=lambda msg: self._failed.emit(rid, msg),
        )

    # ----------------------------------------------------------------- respuestas
    def _store_error(self, message: str) -> None:
        self._pending = False
        self._timeout.stop()
        header = f"Error · {self._header_base}" if self._header_base else "Error"
        self.last = Result(header, message, error=True)
        log.warning("%s", message)

    @Slot(int, object)
    def _on_piece(self, rid: int, piece: StreamPiece) -> None:
        if rid != self._rid:
            return  # respuesta de una captura anterior
        if piece.text:
            self._text += piece.text
        if piece.citations:
            self._citations.extend(piece.citations)

    @Slot(int, object)
    def _on_done(self, rid: int, timing: Timing | None) -> None:
        if rid != self._rid:
            return
        self._pending = False
        self._timeout.stop()
        elapsed = self._clock() - self._started
        self.last = Result(f"{self._header_base} · {_fmt_seconds(elapsed)}", self._text,
                           citations=list(self._citations))
        if timing is not None:
            first = f"{timing.first_text:.2f}s" if timing.first_text is not None else "-"
            log.info("Respuesta: total %.2fs · primer texto %s · %d caracteres",
                     timing.total, first, len(self._text))
        if self.state == WAITING:
            self.icon.fade_out()
            self.band.show_answer(self.last.header, self.last.text, self.last.citations)
            self._set_state(SHOWING)
        # Si el usuario canceló la espera, se guarda en silencio (pulsación larga).

    @Slot(int, str)
    def _on_failed(self, rid: int, message: str) -> None:
        if rid != self._rid:
            return
        self._store_error(message)
        if self.state == WAITING:
            self.icon.flash_error(ERROR_HOLD_MS)
            self._set_state(IDLE)

    def _on_timeout(self) -> None:
        if not self._pending:
            return
        self._rid += 1  # lo que llegue después se descarta
        secs = max(5, int(self._settings().wait_timeout_s))
        self._store_error(f"Gemini no ha respondido en {secs} s.")
        if self.state == WAITING:
            self.icon.flash_error(ERROR_HOLD_MS)
            self._set_state(IDLE)
