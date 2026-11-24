"""Ajustes nativos de Windows para que la franja conviva con OBS.

- WDA_EXCLUDEFROMCAPTURE: la ventana no aparece en ninguna captura (OBS, BitBlt,
  Windows Graphics Capture, Desktop Duplication). Requiere Windows 10 2004+.
- WS_EX_NOACTIVATE / WS_EX_TRANSPARENT / WS_EX_TOOLWINDOW: no roba el foco, deja
  pasar los clics y no aparece en la barra de tareas ni en Alt+Tab.

Fuera de Windows todas las funciones son no-ops y devuelven False.
"""

from __future__ import annotations

import sys

IS_WINDOWS = sys.platform == "win32"

WDA_NONE = 0x00
WDA_EXCLUDEFROMCAPTURE = 0x11

GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

HWND_TOPMOST = -1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010

_user32 = None


def _u32():
    global _user32
    if _user32 is None:
        import ctypes
        from ctypes import wintypes

        u = ctypes.WinDLL("user32", use_last_error=True)
        u.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
        u.SetWindowDisplayAffinity.restype = wintypes.BOOL
        u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, wintypes.UINT]
        u.SetWindowPos.restype = wintypes.BOOL
        get_long = getattr(u, "GetWindowLongPtrW", None) or u.GetWindowLongW
        set_long = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
        get_long.argtypes = [wintypes.HWND, ctypes.c_int]
        get_long.restype = ctypes.c_ssize_t
        set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
        set_long.restype = ctypes.c_ssize_t
        u._get_long = get_long
        u._set_long = set_long
        _user32 = u
    return _user32


def set_exclude_from_capture(hwnd: int, enabled: bool = True) -> bool:
    """Excluye (o vuelve a incluir) la ventana de cualquier captura de pantalla."""
    if not IS_WINDOWS or not hwnd:
        return False
    try:
        return bool(_u32().SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE if enabled else WDA_NONE))
    except Exception:
        return False


def apply_overlay_styles(hwnd: int) -> bool:
    """Sin foco, transparente al ratón y fuera de la barra de tareas/Alt+Tab."""
    if not IS_WINDOWS or not hwnd:
        return False
    try:
        u = _u32()
        style = u._get_long(hwnd, GWL_EXSTYLE)
        u._set_long(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW)
        return True
    except Exception:
        return False


def bring_topmost(hwnd: int) -> bool:
    """Reafirma 'siempre encima' sin activar la ventana (no quita el foco a nadie)."""
    if not IS_WINDOWS or not hwnd:
        return False
    try:
        return bool(_u32().SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE))
    except Exception:
        return False
