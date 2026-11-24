"""La franja superpuesta: sin foco, transparente al ratón, invisible para OBS y
autoajustada al tamaño de la respuesta (nunca hay que hacer scroll)."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetrics,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPalette,
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


# --------------------------------------------------------------------------- ventana


class OverlayWindow(QWidget):
    LOADING = "loading"
    TEXT = "text"
    ERROR = "error"

    def __init__(self, settings_provider: Callable[[], Settings]):
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
        self.setWindowTitle("Overlay Gemini")

        self._settings = settings_provider
        self._header = ""
        self._body = ""
        self._kind = self.TEXT
        self._citations: list[Citation] = []
        self._fit: FitResult | None = None
        self._doc: QTextDocument | None = None
        self._dots = 0
        self.capture_excluded = False

        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.setInterval(33)  # ~30 recolocaciones/s como máximo
        self._relayout_timer.timeout.connect(self._relayout)

        self._dots_timer = QTimer(self)
        self._dots_timer.setInterval(380)
        self._dots_timer.timeout.connect(self._tick_dots)

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

    # ----------------------------------------------------------------- API
    def is_shown(self) -> bool:
        return self.isVisible()

    def has_content(self) -> bool:
        return bool(self._header or self._body)

    def begin(self, header: str) -> None:
        self._header = header
        self._body = ""
        self._citations = []
        self._kind = self.LOADING
        self._dots = 0
        self._dots_timer.start()
        self.show_overlay()

    def set_header(self, header: str) -> None:
        self._header = header
        self._schedule()

    def set_body(self, markdown: str) -> None:
        if self._kind == self.LOADING:
            self._dots_timer.stop()
        self._kind = self.TEXT
        self._body = markdown
        self._schedule()

    def add_citations(self, citations: list[Citation]) -> None:
        known = {c.url for c in self._citations}
        for c in citations:
            if c.url not in known:
                self._citations.append(c)
                known.add(c.url)
        self._schedule()

    def finish(self, header: str) -> None:
        self._dots_timer.stop()
        if self._kind == self.LOADING:
            self._kind = self.TEXT
            self._body = self._body or "*(Gemini no ha devuelto texto)*"
        self._header = header
        self._schedule()

    def show_message(self, header: str, message: str, error: bool = False, show: bool = True) -> None:
        self._dots_timer.stop()
        self._header = header
        self._body = message
        self._citations = []
        self._kind = self.ERROR if error else self.TEXT
        if show:
            self.show_overlay()

    def show_overlay(self) -> None:
        self._relayout()
        self.show()
        self.raise_()
        win32.bring_topmost(self.hwnd())

    def hide_overlay(self) -> None:
        self.hide()

    def body_text(self) -> str:
        return self._body

    def last_fit(self) -> FitResult | None:
        return self._fit

    # ----------------------------------------------------------------- layout
    def _schedule(self) -> None:
        if self.isVisible() and not self._relayout_timer.isActive():
            self._relayout_timer.start()

    def _tick_dots(self) -> None:
        self._dots = (self._dots + 1) % 4
        self._schedule()

    def _display_markdown(self) -> str:
        if self._kind == self.LOADING:
            return "*Analizando" + "." * self._dots + "*"
        return self._body

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
            host = c.title or urlparse(c.url).netloc
            host = host.removeprefix("www.")
            if host and host not in hosts:
                hosts.append(host)
        return "Fuentes: " + " · ".join(hosts[:4])

    def _relayout(self) -> None:
        settings = self._settings()
        style = settings.overlay
        screen = find_screen(settings.screen_name)
        geo = screen.geometry()

        hf = self._header_font(style.font_px)
        hfm = QFontMetrics(hf)
        header_h = hfm.height() + GAP if self._header else 0
        header_w = hfm.horizontalAdvance(self._header) + 4 if self._header else 0
        footer = self._footer_text()
        ffm = QFontMetrics(self._header_font(style.font_px))
        footer_h = ffm.height() + GAP if footer else 0

        measure, docs = document_measure(self._display_markdown())
        fit = fit_layout(measure, geo.width(), geo.height(), style, header_h, header_w, footer_h)
        doc = docs.get(fit.font_px) or make_document(self._display_markdown(), fit.font_px)
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
        settings = self._settings()
        style = settings.overlay
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, RADIUS, RADIUS)
        bg = QColor(14, 16, 21)
        bg.setAlphaF(max(0.2, min(1.0, style.opacity)))
        p.fillPath(path, bg)
        border = QColor(COLOR_ERROR if self._kind == self.ERROR else COLOR_ACCENT)
        border.setAlphaF(0.35)
        p.setPen(border)
        p.drawPath(path)

        y = PAD_Y
        width = self._fit.content_width
        if self._header:
            p.setFont(self._header_font(style.font_px))
            p.setPen(COLOR_ERROR if self._kind == self.ERROR else COLOR_MUTED)
            fm = p.fontMetrics()
            p.drawText(PAD_X, y + fm.ascent(), fm.elidedText(self._header, Qt.TextElideMode.ElideRight, width))
            y += self._header_h

        body_h = self.height() - y - PAD_Y - self._footer_h
        p.save()
        p.translate(PAD_X, y)
        clip = QRectF(0, 0, width, body_h)
        p.setClipRect(clip)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        color = COLOR_ERROR if self._kind == self.ERROR else (
            COLOR_MUTED if self._kind == self.LOADING else COLOR_TEXT)
        ctx.palette.setColor(QPalette.ColorRole.Text, color)
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
            f = self._header_font(style.font_px)
            p.setFont(f)
            note = "… respuesta recortada (demasiado larga)"
            fm = p.fontMetrics()
            p.drawText(PAD_X + width - fm.horizontalAdvance(note), int(y + body_h - 4), note)

        if self._footer:
            p.setFont(self._header_font(style.font_px))
            p.setPen(COLOR_MUTED)
            fm = p.fontMetrics()
            fy = self.height() - PAD_Y - fm.descent()
            p.drawText(PAD_X, fy, fm.elidedText(self._footer, Qt.TextElideMode.ElideRight, width))
        p.end()
