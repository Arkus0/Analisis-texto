"""Captura del monitor elegido usando Qt (mismo QScreen que usa la franja).

Se envía en JPEG de alta calidad: pesa ~10 veces menos que un PNG de pantalla
completa, así la subida es casi instantánea y el texto sigue siendo nítido.
"""

from __future__ import annotations

from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QScreen

MIME_TYPE = "image/jpeg"
JPEG_QUALITY = 90


class CaptureError(Exception):
    pass


def find_screen(name: str) -> QScreen:
    screens = QGuiApplication.screens()
    for s in screens:
        if name and s.name() == name:
            return s
    primary = QGuiApplication.primaryScreen()
    if primary is None and screens:
        primary = screens[0]
    if primary is None:
        raise CaptureError("No se detecta ninguna pantalla.")
    return primary


def describe_screen(s: QScreen, index: int) -> str:
    g = s.geometry()
    dpr = s.devicePixelRatio()
    w, h = round(g.width() * dpr), round(g.height() * dpr)
    primary = " (principal)" if s == QGuiApplication.primaryScreen() else ""
    model = s.model() or s.manufacturer() or ""
    model = f" · {model}" if model else ""
    return f"Pantalla {index + 1}: {w}×{h}{model}{primary}"


def encode_image(img: QImage, max_width: int = 0, fmt: str = "JPG", quality: int = JPEG_QUALITY) -> bytes:
    if img.isNull():
        raise CaptureError("La captura de pantalla ha salido vacía.")
    if max_width and img.width() > max_width:
        img = img.scaledToWidth(max_width, Qt.TransformationMode.SmoothTransformation)
    if fmt.upper() in ("JPG", "JPEG"):
        img = img.convertToFormat(QImage.Format.Format_RGB888)
    buf = QBuffer()
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    if not img.save(buf, fmt, quality):
        raise CaptureError(f"No se pudo codificar la captura en {fmt}.")
    return bytes(buf.data())


def grab_screen(screen_name: str, max_width: int = 0) -> bytes:
    """Captura la pantalla completa a resolución nativa y la devuelve en JPEG."""
    screen = find_screen(screen_name)
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        raise CaptureError("No se pudo capturar la pantalla.")
    return encode_image(pixmap.toImage(), max_width)
