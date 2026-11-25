"""Une todas las fuentes de entrada y las pasa al hilo de la interfaz.

El mando se lee siempre (SDL, sin hooks). Los hooks globales de ratón/teclado solo
se instalan si el botón asignado es de ratón o teclado, o mientras se asigna uno.
"""

from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from ..config import Binding, Settings
from .bindings import VK_ESCAPE, InputEvent, matches
from .gamepad import GamepadListener
from .mouse_kb import MouseKeyboardListener

log = logging.getLogger("overlay_gemini")

HOOK_KINDS = ("mouse", "keyboard")


class InputHub(QObject):
    raw_event = Signal(object)  # emitida desde hilos de entrada → cola de Qt
    capture_pressed = Signal()
    capture_released = Signal()
    learned = Signal(object)  # Binding
    learn_cancelled = Signal()

    def __init__(
        self,
        settings_provider: Callable[[], Settings],
        gamepad_factory=GamepadListener,
        mouse_kb_factory=MouseKeyboardListener,
    ):
        super().__init__()
        self._settings = settings_provider
        self.learning = False
        self.errors: list[str] = []
        self._hook_errors: list[str] = []
        self.gamepad = gamepad_factory(self.raw_event.emit)
        self.mouse_kb = mouse_kb_factory(
            self.raw_event.emit,
            binding=lambda: self._settings().capture_binding,
            learning=lambda: self.learning,
        )
        self.raw_event.connect(self._on_event)

    # ----------------------------------------------------------------- ciclo de vida
    def start(self) -> list[str]:
        err = self.gamepad.start()
        self.errors = [err] if err else []
        self.sync_hooks()
        return self.errors + self._hook_errors

    def stop(self) -> None:
        self.gamepad.stop()
        self.mouse_kb.stop()

    def hooks_needed(self) -> bool:
        b = self._settings().capture_binding
        return self.learning or (b is not None and b.kind in HOOK_KINDS)

    def sync_hooks(self) -> None:
        """Instala o quita los hooks de ratón/teclado según haga falta."""
        want = self.hooks_needed()
        if want and not self.mouse_kb.running:
            self._hook_errors = self.mouse_kb.start()
            log.info("Hooks de ratón/teclado activados")
        elif not want and self.mouse_kb.running:
            self.mouse_kb.stop()
            self._hook_errors = []
            log.info("Hooks de ratón/teclado desactivados (no hacen falta)")

    def all_errors(self) -> list[str]:
        return self.errors + self._hook_errors

    # ----------------------------------------------------------------- asignar botón
    def begin_learn(self) -> None:
        self.learning = True
        self.sync_hooks()

    def cancel_learn(self) -> None:
        self.learning = False
        self.sync_hooks()

    @Slot(object)
    def _on_event(self, ev: InputEvent) -> None:
        if self.learning:
            if not ev.pressed:
                return
            self.learning = False
            if ev.kind == "keyboard" and ev.code == f"vk:{VK_ESCAPE}":
                self.learn_cancelled.emit()
            else:
                self.learned.emit(Binding(kind=ev.kind, code=ev.code, label=ev.label))
            self.sync_hooks()
            return
        if matches(self._settings().capture_binding, ev):
            if ev.pressed:
                self.capture_pressed.emit()
            else:
                self.capture_released.emit()
