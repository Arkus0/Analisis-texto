"""Captura del monitor elegido usando Qt (mismo QScreen que usa la franja).

Dos fases para no bloquear nada:
1. `grab_image()` en el hilo de la interfaz: una única copia de pantalla (~como Impr Pant).
2. `prepare_image()` en el hilo de la petición: recorte de la zona, escalado y JPEG.

Se envía en JPEG de alta calidad: pesa ~10 veces menos que un PNG de pantalla
completa, así la subida es casi instantánea y el texto sigue siendo nítido.
"""

from __future__ import annotations

from typing import Sequence

from PySide6.QtCore import QBuffer, QIODevice, QRect, Qt
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


def crop_rect(width: int, height: int, region: Sequence[float] | None) -> tuple[int, int, int, int]:
    """Convierte una zona en fracciones [x, y, w, h] a píxeles dentro de la imagen."""
    if not region:
        return 0, 0, width, height
    fx, fy, fw, fh = (float(v) for v in region)
    x = min(max(round(fx * width), 0), max(width - 1, 0))
    y = min(max(round(fy * height), 0), max(height - 1, 0))
    w = max(1, min(round(fw * width), width - x))
    h = max(1, min(round(fh * height), height - y))
    return x, y, w, h


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


def prepare_image(img: QImage, region: Sequence[float] | None, max_width: int = 0) -> bytes:
    """Recorta la zona elegida, escala y codifica. Seguro en cualquier hilo (QImage)."""
    if img.isNull():
        raise CaptureError("La captura de pantalla ha salido vacía.")
    if region:
        x, y, w, h = crop_rect(img.width(), img.height(), region)
        img = img.copy(QRect(x, y, w, h))
    return encode_image(img, max_width)


def grab_image(screen_name: str) -> QImage:
    """Copia la pantalla completa a resolución nativa (hilo de la interfaz)."""
    screen = find_screen(screen_name)
    pixmap = screen.grabWindow(0)
    if pixmap.isNull():
        raise CaptureError("No se pudo capturar la pantalla.")
    return pixmap.toImage()


def grab_screen(screen_name: str, max_width: int = 0, region: Sequence[float] | None = None) -> bytes:
    """Atajo síncrono: captura + recorte + JPEG."""
    return prepare_image(grab_image(screen_name), region, max_width)
