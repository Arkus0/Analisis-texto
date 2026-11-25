"""Selector de zona de captura: imagen congelada de la pantalla + rectángulo.

Útil si ves el curso dentro de la ventana de OBS maximizada: marcas la vista
previa una vez y la app solo envía esa zona a Gemini. Se usa solo al configurar.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QScreen
from PySide6.QtWidgets import QWidget

from .config import normalize_region

HINT = "Arrastra para marcar la zona del curso  ·  Intro: aceptar  ·  Esc: cancelar"


def rect_to_region(rect: QRect, width: int, height: int) -> list[float] | None:
    """Rectángulo en píxeles del widget → fracciones [x, y, w, h] (o None si es mínimo)."""
    r = rect.normalized().intersected(QRect(0, 0, width, height))
    if width <= 0 or height <= 0 or r.isEmpty():
        return None
    return normalize_region([r.x() / width, r.y() / height, r.width() / width, r.height() / height])


class RegionPicker(QWidget):
    picked = Signal(object)  # list[float] = zona · None = pantalla completa · "cancel"

    def __init__(self, screen: QScreen, initial: list[float] | None = None):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.Tool)
        self.setWindowTitle("Elegir zona de captura")
        self.setCursor(Qt.CursorShape.CrossCursor)
        self._snapshot: QPixmap = screen.grabWindow(0)
        self.setGeometry(screen.geometry())
        self._origin: QPoint | None = None
        self._rect = QRect()
        self._done = False
        if initial:
            g = screen.geometry()
            x, y, w, h = initial
            self._rect = QRect(round(x * g.width()), round(y * g.height()),
                               round(w * g.width()), round(h * g.height()))

    def region(self) -> list[float] | None:
        return rect_to_region(self._rect, self.width(), self.height())

    # ----------------------------------------------------------------- ratón y teclado
    def mousePressEvent(self, e):  # noqa: N802 (Qt)
        if e.button() == Qt.MouseButton.LeftButton:
            self._origin = e.position().toPoint()
            self._rect = QRect(self._origin, self._origin)
            self.update()

    def mouseMoveEvent(self, e):  # noqa: N802 (Qt)
        if self._origin is not None:
            self._rect = QRect(self._origin, e.position().toPoint()).normalized()
            self.update()

    def mouseReleaseEvent(self, e):  # noqa: N802 (Qt)
        self._origin = None

    def mouseDoubleClickEvent(self, e):  # noqa: N802 (Qt)
        self._finish(self.region())

    def keyPressEvent(self, e):  # noqa: N802 (Qt)
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._finish(self.region())
        elif e.key() == Qt.Key.Key_Escape:
            self._finish(None, cancelled=True)

    def _finish(self, region, cancelled: bool = False) -> None:
        if self._done:
            return
        self._done = True
        self.picked.emit("cancel" if cancelled else region)
        self.close()

    # ----------------------------------------------------------------- pintado
    def paintEvent(self, event):  # noqa: N802 (Qt)
        p = QPainter(self)
        p.drawPixmap(self.rect(), self._snapshot)
        shade = QColor(0, 0, 0, 140)
        r = self._rect.normalized()
        if r.isEmpty():
            p.fillRect(self.rect(), shade)
        else:
            # Oscurece todo menos la zona elegida.
            full = QRect(self.rect())
            p.fillRect(QRect(full.left(), full.top(), full.width(), r.top() - full.top()), shade)
            p.fillRect(QRect(full.left(), r.bottom() + 1, full.width(), full.bottom() - r.bottom()), shade)
            p.fillRect(QRect(full.left(), r.top(), r.left() - full.left(), r.height()), shade)
            p.fillRect(QRect(r.right() + 1, r.top(), full.right() - r.right(), r.height()), shade)
            p.setPen(QPen(QColor("#7CC4FF"), 2))
            p.drawRect(r)
            size = f"{r.width()}×{r.height()}"
            p.setPen(QColor("white"))
            p.drawText(r.adjusted(6, 4, 0, 0), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, size)

        f = QFont()
        f.setPixelSize(18)
        f.setBold(True)
        p.setFont(f)
        fm = p.fontMetrics()
        w = fm.horizontalAdvance(HINT) + 32
        box = QRectF((self.width() - w) / 2, 24, w, fm.height() + 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(14, 16, 21, 220))
        p.drawRoundedRect(box, 10, 10)
        p.setPen(QColor("white"))
        p.drawText(box, Qt.AlignmentFlag.AlignCenter, HINT)
        p.end()
