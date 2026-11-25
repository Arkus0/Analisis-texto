"""Eventos de entrada normalizados (mando, joystick, ratón, teclado) y etiquetas."""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Binding

GAMEPAD_LABELS = {
    "a": "A", "b": "B", "x": "X", "y": "Y",
    "back": "Select / Back / −", "guide": "Home / Guide", "start": "Start / +",
    "leftstick": "L3 (pulsar stick izq.)", "rightstick": "R3 (pulsar stick der.)",
    "leftshoulder": "L / LB / L1", "rightshoulder": "R / RB / R1",
    "lefttrigger": "ZL / LT / L2", "righttrigger": "ZR / RT / R2",
    "dpup": "Cruceta ↑", "dpdown": "Cruceta ↓", "dpleft": "Cruceta ←", "dpright": "Cruceta →",
    "misc1": "Captura / Share / Mic", "touchpad": "Panel táctil",
    "paddle1": "Paleta 1", "paddle2": "Paleta 2", "paddle3": "Paleta 3", "paddle4": "Paleta 4",
}

MOUSE_LABELS = {
    "x1": "Ratón: botón lateral trasero (X1)",
    "x2": "Ratón: botón lateral delantero (X2)",
    "middle": "Ratón: botón central (rueda)",
}

VK_ESCAPE = 0x1B

_VK_NAMES = {
    0x08: "Retroceso", 0x09: "Tab", 0x0D: "Intro", 0x13: "Pausa", 0x14: "Bloq Mayús",
    0x20: "Espacio", 0x21: "Re Pág", 0x22: "Av Pág", 0x23: "Fin", 0x24: "Inicio",
    0x25: "←", 0x26: "↑", 0x27: "→", 0x28: "↓", 0x2C: "Impr Pant", 0x2D: "Insert",
    0x2E: "Supr", 0x90: "Bloq Num", 0x91: "Bloq Despl",
    0xAD: "Silenciar", 0xAE: "Volumen −", 0xAF: "Volumen +",
    0xB0: "Multimedia: siguiente", 0xB1: "Multimedia: anterior", 0xB3: "Multimedia: play/pausa",
}


def vk_name(vk: int) -> str:
    if 0x70 <= vk <= 0x87:
        return f"F{vk - 0x6F}"
    if 0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A:
        return chr(vk)
    if 0x60 <= vk <= 0x69:
        return f"Num {vk - 0x60}"
    return _VK_NAMES.get(vk, f"VK 0x{vk:02X}")


def gamepad_label(name: str) -> str:
    return f"Mando: {GAMEPAD_LABELS.get(name, name)}"


@dataclass(frozen=True)
class InputEvent:
    kind: str  # gamepad | joystick | mouse | keyboard
    code: str
    pressed: bool
    label: str = ""

    def to_binding(self) -> Binding:
        return Binding(kind=self.kind, code=self.code, label=self.label)


def matches(binding: Binding | None, event: InputEvent) -> bool:
    return binding is not None and binding.kind == event.kind and binding.code == event.code


def keyboard_event(vk: int, pressed: bool) -> InputEvent:
    return InputEvent("keyboard", f"vk:{vk}", pressed, f"Tecla: {vk_name(vk)}")


def mouse_event(code: str, pressed: bool) -> InputEvent:
    return InputEvent("mouse", code, pressed, MOUSE_LABELS.get(code, f"Ratón: {code}"))
