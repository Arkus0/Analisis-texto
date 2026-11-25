"""Botones del ratón (X1, X2, central) y teclas globales con pynput.

Los hooks globales SOLO se instalan cuando hacen falta (botón asignado de ratón o
teclado, o mientras se asigna un botón). Con el mando no hay ningún hook, así que
el ratón y el teclado del sistema no pasan nunca por esta app.

En Windows el botón/tecla asignado se SUPRIME: no llega a ninguna otra
aplicación. Así X1 no hace "Atrás" en el navegador ni la tecla llega a OBS.
"""

from __future__ import annotations

import sys
from typing import Callable

from ..config import Binding
from .bindings import InputEvent, keyboard_event, matches, mouse_event

IS_WINDOWS = sys.platform == "win32"

WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x0100, 0x0101, 0x0104, 0x0105
WM_MBUTTONDOWN, WM_MBUTTONUP = 0x0207, 0x0208
WM_XBUTTONDOWN, WM_XBUTTONUP = 0x020B, 0x020C


def decode_mouse_msg(msg: int, mouse_data: int) -> InputEvent | None:
    if msg in (WM_XBUTTONDOWN, WM_XBUTTONUP):
        which = (mouse_data >> 16) & 0xFFFF
        code = "x1" if which == 1 else "x2" if which == 2 else None
        if code is None:
            return None
        return mouse_event(code, msg == WM_XBUTTONDOWN)
    if msg in (WM_MBUTTONDOWN, WM_MBUTTONUP):
        return mouse_event("middle", msg == WM_MBUTTONDOWN)
    return None


def decode_key_msg(msg: int, vk: int) -> InputEvent | None:
    if msg in (WM_KEYDOWN, WM_SYSKEYDOWN):
        return keyboard_event(vk, True)
    if msg in (WM_KEYUP, WM_SYSKEYUP):
        return keyboard_event(vk, False)
    return None


class MouseKeyboardListener:
    def __init__(
        self,
        emit: Callable[[InputEvent], None],
        binding: Callable[[], Binding | None],
        learning: Callable[[], bool],
    ):
        self._emit = emit
        self._binding = binding
        self._learning = learning
        self._mouse = None
        self._keyboard = None

    # Decide si un evento nos interesa: el asignado, o cualquiera en modo aprendizaje.
    def _wanted(self, ev: InputEvent) -> bool:
        return self._learning() or matches(self._binding(), ev)

    # ---------------------------------------------------------------- Windows (hooks con supresión)
    def _win_mouse_filter(self, msg, data):
        ev = decode_mouse_msg(msg, int(getattr(data, "mouseData", 0)))
        if ev is not None and self._wanted(ev):
            self._emit(ev)
            listener = self._mouse
            if listener is not None:
                listener.suppress_event()  # lanza excepción: debe ser lo último
        return True

    def _win_key_filter(self, msg, data):
        ev = decode_key_msg(msg, int(getattr(data, "vkCode", 0)))
        if ev is not None and self._wanted(ev):
            self._emit(ev)
            listener = self._keyboard
            if listener is not None:
                listener.suppress_event()
        return True

    # ---------------------------------------------------------------- otros SO (sin supresión)
    def _on_click(self, x, y, button, pressed):
        code = getattr(button, "name", "")
        if code in ("x1", "x2", "middle", "button8", "button9"):
            code = {"button8": "x1", "button9": "x2"}.get(code, code)
            ev = mouse_event(code, pressed)
            if self._wanted(ev):
                self._emit(ev)

    def _key_vk(self, key) -> int | None:
        vk = getattr(key, "vk", None)
        if vk is None and hasattr(key, "value"):
            vk = getattr(key.value, "vk", None)
        return vk

    def _on_press(self, key):
        vk = self._key_vk(key)
        if vk is not None:
            ev = keyboard_event(vk, True)
            if self._wanted(ev):
                self._emit(ev)

    def _on_release(self, key):
        vk = self._key_vk(key)
        if vk is not None:
            ev = keyboard_event(vk, False)
            if self._wanted(ev):
                self._emit(ev)

    # ---------------------------------------------------------------- ciclo de vida
    @property
    def running(self) -> bool:
        return self._mouse is not None or self._keyboard is not None

    def start(self) -> list[str]:
        if self.running:
            return []
        errors: list[str] = []
        try:
            from pynput import keyboard, mouse
        except Exception as e:  # noqa: BLE001
            return [f"Ratón/teclado no disponibles: {e}"]
        try:
            if IS_WINDOWS:
                self._mouse = mouse.Listener(win32_event_filter=self._win_mouse_filter)
            else:
                self._mouse = mouse.Listener(on_click=self._on_click)
            self._mouse.start()
        except Exception as e:  # noqa: BLE001
            self._mouse = None
            errors.append(f"Ratón: {e}")
        try:
            if IS_WINDOWS:
                self._keyboard = keyboard.Listener(win32_event_filter=self._win_key_filter)
            else:
                self._keyboard = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
            self._keyboard.start()
        except Exception as e:  # noqa: BLE001
            self._keyboard = None
            errors.append(f"Teclado: {e}")
        return errors

    def stop(self) -> None:
        for listener in (self._mouse, self._keyboard):
            try:
                if listener:
                    listener.stop()
            except Exception:
                pass
        self._mouse = self._keyboard = None
