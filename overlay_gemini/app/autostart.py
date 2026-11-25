"""Arrancar con Windows.

Añade (o quita) el valor `OverlayGemini` en
HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run: solo para tu usuario, sin
permisos de administrador y sin ninguna ventana. La app arranca con `--autostart`,
directamente en la bandeja. Fuera de Windows todo es no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "OverlayGemini"
IS_WINDOWS = sys.platform == "win32"


class Registry(Protocol):
    def get(self, name: str) -> str | None: ...
    def set(self, name: str, value: str) -> None: ...
    def delete(self, name: str) -> None: ...


class WinRunKey:
    """La clave Run del usuario actual, con `winreg` (biblioteca estándar)."""

    def get(self, name: str) -> str | None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
                value, _kind = winreg.QueryValueEx(key, name)
                return str(value)
        except FileNotFoundError:
            return None

    def set(self, name: str, value: str) -> None:
        import winreg

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)

    def delete(self, name: str) -> None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            pass


def supported() -> bool:
    return IS_WINDOWS


def _registry(reg: Registry | None) -> Registry | None:
    if reg is not None:
        return reg
    return WinRunKey() if IS_WINDOWS else None


def launch_command(executable: str | None = None, frozen: bool | None = None,
                   script: str | None = None) -> str:
    """Orden que ejecutará Windows al iniciar sesión.

    - `.exe` empaquetado: "C:\\…\\OverlayGemini.exe" --autostart
    - Desde el código:    "…\\pythonw.exe" "…\\main.py" --autostart
      (pythonw en vez de python para que no aparezca ninguna consola)
    """
    executable = executable or sys.executable
    frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    if frozen:
        return f'"{executable}" --autostart'
    exe = Path(executable)
    if exe.name.lower() == "python.exe" and exe.with_name("pythonw.exe").exists():
        exe = exe.with_name("pythonw.exe")
    script = script or str(Path(__file__).resolve().parents[1] / "main.py")
    return f'"{exe}" "{script}" --autostart'


def is_enabled(reg: Registry | None = None, name: str = VALUE_NAME) -> bool:
    r = _registry(reg)
    if r is None:
        return False
    try:
        return bool(r.get(name))
    except OSError:
        return False


def set_enabled(on: bool, reg: Registry | None = None, name: str = VALUE_NAME,
                command: str | None = None) -> bool:
    """Activa o desactiva el arranque. Devuelve False si no aplica (fuera de Windows)."""
    r = _registry(reg)
    if r is None:
        return False
    if on:
        r.set(name, command or launch_command())
    else:
        r.delete(name)
    return True


def refresh_path(reg: Registry | None = None, name: str = VALUE_NAME,
                 command: str | None = None) -> bool:
    """Si está activado y la ruta guardada ya no es la actual (has movido la carpeta
    del .exe), la corrige en silencio. Devuelve True si ha cambiado algo."""
    r = _registry(reg)
    if r is None:
        return False
    try:
        current = r.get(name)
        if not current:
            return False
        wanted = command or launch_command()
        if current != wanted:
            r.set(name, wanted)
            return True
    except OSError:
        pass
    return False
