"""Lectura de mandos con SDL2 en un hilo propio, también en segundo plano.

SDL reconoce 8BitDo, Switch Pro, Joy-Con, DualShock 4, DualSense, Xbox y
cientos más como "game controller"; los dispositivos raros (arcade, botoneras)
se leen como joystick genérico (botón N).
"""

from __future__ import annotations

import ctypes
import threading
import time
from typing import Callable

from .bindings import InputEvent, gamepad_label

TRIGGER_PRESS = 16000
TRIGGER_RELEASE = 8000
POLL_S = 0.010  # 100 Hz: de sobra para un botón y casi sin CPU


class GamepadListener:
    def __init__(self, emit: Callable[[InputEvent], None]):
        self._emit = emit
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self.error: str | None = None
        self.connected: dict[int, str] = {}  # instance id -> nombre
        # Solo se abren mandos/joysticks (HID). Nunca cámaras ni capturadoras como
        # la Cam Link: SDL no toca dispositivos de vídeo.

    def start(self) -> str | None:
        self._thread = threading.Thread(target=self._run, name="sdl-gamepad", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)
        return self.error

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)

    def _run(self) -> None:
        try:
            import sdl2
        except Exception as e:  # noqa: BLE001
            self.error = f"SDL2 no disponible: {e}"
            self._ready.set()
            return

        sdl2.SDL_SetHint(b"SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", b"1")  # leer sin foco
        sdl2.SDL_SetHint(b"SDL_TIMER_RESOLUTION", b"0")  # no tocar el temporizador del sistema
        if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK) != 0:
            self.error = "No se pudo iniciar SDL: " + (sdl2.SDL_GetError() or b"").decode(errors="replace")
            self._ready.set()
            return
        self._ready.set()

        controllers: dict[int, object] = {}
        joysticks: dict[int, object] = {}
        triggers: dict[tuple[int, int], bool] = {}
        ev = sdl2.SDL_Event()

        def open_controller(index: int) -> None:
            pad = sdl2.SDL_GameControllerOpen(index)
            if not pad:
                return
            joy = sdl2.SDL_GameControllerGetJoystick(pad)
            iid = sdl2.SDL_JoystickInstanceID(joy)
            if iid in controllers:
                sdl2.SDL_GameControllerClose(pad)
                return
            controllers[iid] = pad
            name = sdl2.SDL_GameControllerName(pad)
            self.connected[iid] = (name or b"Mando").decode(errors="replace")

        def open_joystick(index: int) -> None:
            if sdl2.SDL_IsGameController(index):
                return  # se abre como game controller
            joy = sdl2.SDL_JoystickOpen(index)
            if not joy:
                return
            iid = sdl2.SDL_JoystickInstanceID(joy)
            if iid in joysticks:
                sdl2.SDL_JoystickClose(joy)
                return
            joysticks[iid] = joy
            name = sdl2.SDL_JoystickName(joy)
            self.connected[iid] = (name or b"Joystick").decode(errors="replace")

        try:
            while not self._stop.is_set():
                while sdl2.SDL_PollEvent(ctypes.byref(ev)):
                    t = ev.type
                    if t == sdl2.SDL_CONTROLLERDEVICEADDED:
                        open_controller(ev.cdevice.which)
                    elif t == sdl2.SDL_JOYDEVICEADDED:
                        open_joystick(ev.jdevice.which)
                    elif t == sdl2.SDL_CONTROLLERDEVICEREMOVED:
                        pad = controllers.pop(ev.cdevice.which, None)
                        if pad:
                            sdl2.SDL_GameControllerClose(pad)
                        self.connected.pop(ev.cdevice.which, None)
                    elif t == sdl2.SDL_JOYDEVICEREMOVED:
                        joy = joysticks.pop(ev.jdevice.which, None)
                        if joy:
                            sdl2.SDL_JoystickClose(joy)
                            self.connected.pop(ev.jdevice.which, None)
                    elif t in (sdl2.SDL_CONTROLLERBUTTONDOWN, sdl2.SDL_CONTROLLERBUTTONUP):
                        raw = sdl2.SDL_GameControllerGetStringForButton(ev.cbutton.button)
                        name = (raw or b"").decode() or f"button{ev.cbutton.button}"
                        self._emit(InputEvent("gamepad", name, t == sdl2.SDL_CONTROLLERBUTTONDOWN,
                                              gamepad_label(name)))
                    elif t == sdl2.SDL_CONTROLLERAXISMOTION:
                        axis = ev.caxis.axis
                        if axis in (sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT):
                            key = (ev.caxis.which, axis)
                            down = triggers.get(key, False)
                            value = ev.caxis.value
                            if not down and value > TRIGGER_PRESS or down and value < TRIGGER_RELEASE:
                                triggers[key] = not down
                                name = (sdl2.SDL_GameControllerGetStringForAxis(axis) or b"").decode()
                                self._emit(InputEvent("gamepad", name, not down, gamepad_label(name)))
                    elif t in (sdl2.SDL_JOYBUTTONDOWN, sdl2.SDL_JOYBUTTONUP):
                        if ev.jbutton.which in joysticks:  # los game controllers ya se tratan arriba
                            n = ev.jbutton.button
                            self._emit(InputEvent("joystick", str(n), t == sdl2.SDL_JOYBUTTONDOWN,
                                                  f"Joystick: botón {n + 1}"))
                time.sleep(POLL_S)
        finally:
            for pad in controllers.values():
                sdl2.SDL_GameControllerClose(pad)
            for joy in joysticks.values():
                sdl2.SDL_JoystickClose(joy)
            sdl2.SDL_Quit()
