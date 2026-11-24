"""Une todas las fuentes de entrada y las pasa al hilo de la interfaz."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from ..config import Binding, Settings
from .bindings import VK_ESCAPE, InputEvent, matches
from .gamepad import GamepadListener
from .mouse_kb import MouseKeyboardListener


class InputHub(QObject):
    raw_event = Signal(object)  # emitida desde hilos de entrada → cola de Qt
    capture_pressed = Signal()
    capture_released = Signal()
    learned = Signal(object)  # Binding
    learn_cancelled = Signal()

    def __init__(self, settings_provider: Callable[[], Settings]):
        super().__init__()
        self._settings = settings_provider
        self.learning = False
        self.errors: list[str] = []
        self.gamepad = GamepadListener(self.raw_event.emit)
        self.mouse_kb = MouseKeyboardListener(
            self.raw_event.emit,
            binding=lambda: self._settings().capture_binding,
            learning=lambda: self.learning,
        )
        self.raw_event.connect(self._on_event)

    def start(self) -> list[str]:
        self.errors = []
        err = self.gamepad.start()
        if err:
            self.errors.append(err)
        self.errors.extend(self.mouse_kb.start())
        return self.errors

    def stop(self) -> None:
        self.gamepad.stop()
        self.mouse_kb.stop()

    def begin_learn(self) -> None:
        self.learning = True

    def cancel_learn(self) -> None:
        self.learning = False

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
            return
        if matches(self._settings().capture_binding, ev):
            if ev.pressed:
                self.capture_pressed.emit()
            else:
                self.capture_released.emit()
