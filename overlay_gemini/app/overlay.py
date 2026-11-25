"""Ventanas superpuestas: el icono de espera y la franja con la respuesta.

Ambas son "fantasma": sin foco, transparentes al ratón, invisibles para OBS y con
fundidos que solo cambian la opacidad. La franja se autoajusta al tamaño de la
respuesta (nunca hay que hacer scroll) y se maqueta una sola vez."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
    QPen,
    QTextBlockFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import QWidget

from . import win32
from .capture import find_screen
from .config import OverlayStyle, Settings
from .gemini_client import Citation

PAD_X = 22
PAD_Y = 14
GAP = 6
RADIUS = 14
MIN_TOTAL_H = 72
LINE_HEIGHT_PCT = 118

FONT_FAMILY = "Segoe UI"

COLOR_TEXT = QColor("#F3F5F8")
COLOR_MUTED = QColor("#9DA7B5")
COLOR_ERROR = QColor("#FF9A8F")
COLOR_ACCENT = QColor("#7CC4FF")


# --------------------------------------------------------------------------- ajuste (puro)


@dataclass
class FitResult:
    width: int
    height: int
    font_px: int
    content_width: int
    truncated: bool


Measure = Callable[[int, int], tuple[float, float]]  # (ancho de texto, px fuente) -> (ideal, alto)


def fit_layout(
    measure: Measure,
    avail_w: int,
    avail_h: int,
    style: OverlayStyle,
    header_h: int,
    header_w: int = 0,
    footer_h: int = 0,
) -> FitResult:
    """Calcula el tamaño de la franja para que el texto quepa entero.

    1. Ancho = el que necesita el texto, hasta `max_width`.
    2. Alto = el del texto, hasta `max_height`.
    3. Si no cabe: se ensancha hasta `wide_width`; luego se reduce la letra
       poco a poco hasta `min_font_ratio`.
    4. Si aun así no cabe: tamaño máximo y `truncated=True`.
    """
    max_w = min(avail_w, max(style.min_width_px, int(avail_w * style.max_width)))
    wide_w = min(avail_w, max(max_w, int(avail_w * style.wide_width)))
    max_h = max(MIN_TOTAL_H, int(avail_h * style.max_height))
    base = max(8, int(style.font_px))
    min_font = max(8, min(base, int(round(base * style.min_font_ratio))))
    chrome_h = 2 * PAD_Y + header_h + footer_h
    caps = [max_w] if wide_w == max_w else [max_w, wide_w]
    step = max(1, round(base * 0.05))

    font = base
    while True:
        for cap in caps:
            ideal, body_h = measure(cap - 2 * PAD_X, font)
            total_h = chrome_h + math.ceil(body_h)
            if total_h <= max_h:
                want = max(math.ceil(ideal), header_w) + 2 * PAD_X
                width = max(min(style.min_width_px, cap), min(cap, want))
                return FitResult(width, max(MIN_TOTAL_H, total_h), font, width - 2 * PAD_X, False)
        if font <= min_font:
            break
        font = max(min_font, font - step)
    return FitResult(wide_w, max_h, min_font, wide_w - 2 * PAD_X, True)


_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)


def compact_markdown(md: str) -> str:
    """Convierte encabezados en negrita: en una franja los títulos grandes sobran."""
    return _HEADING.sub(lambda m: f"**{m.group(1)}**" if m.group(1) else "", md or "")


def make_document(markdown: str, font_px: int, family: str = FONT_FAMILY) -> QTextDocument:
    doc = QTextDocument()
    font = QFont(family)
    font.setPixelSize(font_px)
    doc.setDefaultFont(font)
    doc.setDocumentMargin(0)
    doc.setMarkdown(compact_markdown(markdown), QTextDocument.MarkdownFeature.MarkdownDialectGitHub)
    # Un poco más de interlineado: se lee mejor de un vistazo sobre el vídeo.
    cursor = QTextCursor(doc)
    cursor.select(QTextCursor.SelectionType.Document)
    fmt = QTextBlockFormat()
    fmt.setLineHeight(LINE_HEIGHT_PCT, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value)
    cursor.mergeBlockFormat(fmt)
    return doc


def document_measure(markdown: str, family: str = FONT_FAMILY) -> tuple[Measure, dict[int, QTextDocument]]:
    cache: dict[int, QTextDocument] = {}

    def measure(width: int, font_px: int) -> tuple[float, float]:
        doc = cache.get(font_px)
        if doc is None:
            doc = cache[font_px] = make_document(markdown, font_px, family)
        doc.setTextWidth(max(1, width))
        return doc.idealWidth(), doc.size().height()

    return measure, cache


# --------------------------------------------------------------------------- ventana base


class GhostWindow(QWidget):
    """Ventana 'fantasma': sin foco, transparente al ratón, siempre encima, invisible
    para OBS y con fundidos que solo cambian la opacidad (no repintan nada)."""

    def __init__(self, settings_provider: Callable[[], Settings], title: str):
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.NoDropShadowWindowHint
        )
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setWindowTitle(title)
        self._settings = settings_provider
        self.capture_excluded = False
        self._fading_out = False
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.finished.connect(self._on_anim_finished)
        self.apply_native()

    # ----------------------------------------------------------------- nativo
    def hwnd(self) -> int:
        return int(self.winId())

    def apply_native(self) -> None:
        hwnd = self.hwnd()  # crea la ventana nativa aunque no esté visible
        win32.apply_overlay_styles(hwnd)
        self.capture_excluded = win32.set_exclude_from_capture(hwnd, self._settings().exclude_from_capture)

    def showEvent(self, event):  # noqa: N802 (Qt)
        super().showEvent(event)
        self.apply_native()
        win32.bring_topmost(self.hwnd())

    # ----------------------------------------------------------------- fundidos
    def _fade_ms(self) -> int:
        return max(0, int(self._settings().overlay.fade_ms))

    def is_shown(self) -> bool:
        """Visible y no desapareciendo (estado lógico, no visual)."""
        return self.isVisible() and not self._fading_out

    def fade_in(self, ms: int | None = None) -> None:
        ms = self._fade_ms() if ms is None else ms
        self._anim.stop()
        self._fading_out = False
        if not self.isVisible():
            self.setWindowOpacity(0.0 if ms else 1.0)
            self.show()
            self.raise_()
            win32.bring_topmost(self.hwnd())
        if ms <= 0:
            self.setWindowOpacity(1.0)
            return
        self._anim.setDuration(ms)
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(1.0)
        self._anim.start()

    def fade_out(self, ms: int | None = None) -> None:
        ms = self._fade_ms() if ms is None else ms
        if not self.isVisible():
            return
        self._anim.stop()
        self._fading_out = True
        if ms <= 0:
            self._on_anim_finished()
            return
        self._anim.setDuration(ms)
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def hide_now(self) -> None:
        self._anim.stop()
        self._fading_out = False
        self.hide()
        self.setWindowOpacity(1.0)
        self._after_hide()

    def _on_anim_finished(self) -> None:
        if self._fading_out:
            self._fading_out = False
            self.hide()
            self._after_hide()

    def _after_hide(self) -> None:
        """Para subclases: parar temporizadores al ocultarse."""

    def anchor_point(self) -> tuple[int, int]:
        """Centro de la franja en coordenadas de pantalla."""
        settings = self._settings()
        geo = find_screen(settings.screen_name).geometry()
        return (geo.x() + geo.width() // 2,
                int(geo.y() + geo.height() * settings.overlay.vertical_center))


# --------------------------------------------------------------------------- icono de espera


class BusyIcon(GhostWindow):
    """Icono pequeño en el centro mientras Gemini prepara la respuesta."""

    SIZE = 64
    FPS = 30

    def __init__(self, settings_provider: Callable[[], Settings]):
        super().__init__(settings_provider, "Overlay Gemini · espera")
        self.setFixedSize(self.SIZE, self.SIZE)
        self._angle = 0.0
        self.error = False
        self._spin = QTimer(self)
        self._spin.setInterval(1000 // self.FPS)
        self._spin.timeout.connect(self._tick)
        self._error_hold = QTimer(self)
        self._error_hold.setSingleShot(True)
        self._error_hold.timeout.connect(lambda: self.fade_out())

    def start(self) -> None:
        """Aparece (fundido) y empieza a girar."""
        self._error_hold.stop()
        self.error = False
        cx, cy = self.anchor_point()
        self.move(cx - self.SIZE // 2, cy - self.SIZE // 2)
        self._spin.start()
        self.update()
        self.fade_in(min(150, self._fade_ms()))

    def flash_error(self, hold_ms: int = 2000) -> None:
        """Se pone rojo, se queda quieto `hold_ms` y desaparece solo."""
        self._spin.stop()
        self.error = True
        self.update()
        if not self.isVisible():
            cx, cy = self.anchor_point()
            self.move(cx - self.SIZE // 2, cy - self.SIZE // 2)
            self.fade_in(min(150, self._fade_ms()))
        self._error_hold.start(hold_ms)

    def _after_hide(self) -> None:
        self._spin.stop()
        self._error_hold.stop()

    def _tick(self) -> None:
        self._angle = (self._angle + 360.0 / self.FPS * 0.9) % 360.0
        self.update()

    def paintEvent(self, event):  # noqa: N802 (Qt)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        bg = QColor(14, 16, 21)
        bg.setAlphaF(0.88)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(bg)
        p.drawEllipse(r)

        accent = QColor(COLOR_ERROR if self.error else COLOR_ACCENT)
        ring = r.adjusted(5, 5, -5, -5)
        pen = QPen(accent, 3.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if self.error:
            p.drawEllipse(ring)
        else:
            faint = QColor(accent)
            faint.setAlphaF(0.18)
            p.setPen(QPen(faint, 3.2))
            p.drawEllipse(ring)
            p.setPen(pen)
            p.drawArc(ring, int(-self._angle * 16), int(100 * 16))

        # destello de 4 puntas en el centro
        c = r.center()
        s = r.width() * 0.17
        star = QPainterPath()
        star.moveTo(c.x(), c.y() - s)
        star.quadTo(c.x(), c.y(), c.x() + s, c.y())
        star.quadTo(c.x(), c.y(), c.x(), c.y() + s)
        star.quadTo(c.x(), c.y(), c.x() - s, c.y())
        star.quadTo(c.x(), c.y(), c.x(), c.y() - s)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(COLOR_ERROR if self.error else COLOR_TEXT))
        p.drawPath(star)
        p.end()


# --------------------------------------------------------------------------- franja


class OverlayWindow(GhostWindow):
    """La franja con la respuesta. Se maqueta UNA vez y entra con un fundido."""

    def __init__(self, settings_provider: Callable[[], Settings]):
        super().__init__(settings_provider, "Overlay Gemini")
        self._header = ""
        self._body = ""
        self._error = False
        self._citations: list[Citation] = []
        self._fit: FitResult | None = None
        self._doc: QTextDocument | None = None
        self._header_h = self._footer_h = 0
        self._footer = ""

    # ----------------------------------------------------------------- API
    def has_content(self) -> bool:
        return bool(self._header or self._body)

    def set_content(self, header: str, markdown: str, citations: list[Citation] | None = None,
                    error: bool = False) -> None:
        self._header = header
        self._body = markdown or "*(Gemini no ha devuelto texto)*"
        self._error = error
        self._citations = []
        known: set[str] = set()
        for c in citations or []:
            if c.url not in known:
                self._citations.append(c)
                known.add(c.url)

    def reveal(self) -> None:
        """Maqueta con el contenido actual y aparece con un fundido."""
        self._relayout()
        self.fade_in()

    def show_answer(self, header: str, markdown: str, citations: list[Citation] | None = None,
                    error: bool = False) -> None:
        self.set_content(header, markdown, citations, error)
        self.reveal()

    def show_message(self, header: str, message: str, error: bool = False, show: bool = True) -> None:
        self.set_content(header, message, None, error)
        if show:
            self.reveal()

    def body_text(self) -> str:
        return self._body

    def last_fit(self) -> FitResult | None:
        return self._fit

    # ----------------------------------------------------------------- layout
    def _header_font(self, base_px: int) -> QFont:
        f = QFont(FONT_FAMILY)
        f.setPixelSize(max(11, round(base_px * 0.62)))
        f.setWeight(QFont.Weight.DemiBold)
        return f

    def _footer_text(self) -> str:
        if not self._citations:
            return ""
        hosts: list[str] = []
        for c in self._citations:
            host = (c.title or urlparse(c.url).netloc).removeprefix("www.")
            if host and host not in hosts:
                hosts.append(host)
        return "Fuentes: " + " · ".join(hosts[:4])

    def _relayout(self) -> None:
        settings = self._settings()
        style = settings.overlay
        geo = find_screen(settings.screen_name).geometry()

        hfm = QFontMetrics(self._header_font(style.font_px))
        header_h = hfm.height() + GAP if self._header else 0
        header_w = hfm.horizontalAdvance(self._header) + 4 if self._header else 0
        footer = self._footer_text()
        footer_h = hfm.height() + GAP if footer else 0

        measure, docs = document_measure(self._body)
        fit = fit_layout(measure, geo.width(), geo.height(), style, header_h, header_w, footer_h)
        doc = docs.get(fit.font_px) or make_document(self._body, fit.font_px)
        doc.setTextWidth(fit.content_width)
        self._doc, self._fit = doc, fit
        self._header_h, self._footer_h, self._footer = header_h, footer_h, footer

        x = geo.x() + (geo.width() - fit.width) // 2
        cy = geo.y() + geo.height() * style.vertical_center
        y = int(cy - fit.height / 2)
        y = max(geo.y(), min(y, geo.y() + geo.height() - fit.height))
        self.setGeometry(x, y, fit.width, fit.height)
        self.update()

    # ----------------------------------------------------------------- pintado
    def paintEvent(self, event):  # noqa: N802 (Qt)
        if self._fit is None or self._doc is None:
            return
        style = self._settings().overlay
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS, RADIUS)
        bg = QColor(14, 16, 21)
        bg.setAlphaF(max(0.2, min(1.0, style.opacity)))
        p.fillPath(path, bg)
        border = QColor(COLOR_ERROR if self._error else COLOR_ACCENT)
        border.setAlphaF(0.35)
        p.setPen(border)
        p.drawPath(path)

        y = PAD_Y
        width = self._fit.content_width
        if self._header:
            p.setFont(self._header_font(style.font_px))
            p.setPen(COLOR_ERROR if self._error else COLOR_MUTED)
            fm = p.fontMetrics()
            p.drawText(PAD_X, y + fm.ascent(), fm.elidedText(self._header, Qt.TextElideMode.ElideRight, width))
            y += self._header_h

        body_h = self.height() - y - PAD_Y - self._footer_h
        p.save()
        p.translate(PAD_X, y)
        clip = QRectF(0, 0, width, body_h)
        p.setClipRect(clip)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        ctx.palette.setColor(QPalette.ColorRole.Text, COLOR_ERROR if self._error else COLOR_TEXT)
        ctx.clip = clip
        self._doc.documentLayout().draw(p, ctx)
        p.restore()

        if self._fit.truncated:
            fade_h = min(48, body_h)
            grad = QLinearGradient(0, y + body_h - fade_h, 0, y + body_h)
            transparent = QColor(bg)
            transparent.setAlpha(0)
            solid = QColor(bg)
            solid.setAlpha(255)
            grad.setColorAt(0, transparent)
            grad.setColorAt(1, solid)
            p.fillRect(QRectF(PAD_X, y + body_h - fade_h, width, fade_h), grad)
            p.setPen(COLOR_ACCENT)
            p.setFont(self._header_font(style.font_px))
            note = "… respuesta recortada (demasiado larga)"
            fm = p.fontMetrics()
            p.drawText(PAD_X + width - fm.horizontalAdvance(note), int(y + body_h - 4), note)

        if self._footer:
            p.setFont(self._header_font(style.font_px))
            p.setPen(COLOR_MUTED)
            fm = p.fontMetrics()
            p.drawText(PAD_X, self.height() - PAD_Y - fm.descent(),
                       fm.elidedText(self._footer, Qt.TextElideMode.ElideRight, width))
        p.end()
