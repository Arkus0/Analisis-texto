import pytest

from app.config import OverlayStyle, default_settings
from app.overlay import PAD_X, PAD_Y, OverlayWindow, compact_markdown, fit_layout

SCREEN_W, SCREEN_H = 1920, 1080


def fake_measure(chars: int, line_h_per_px: float = 1.4, char_w_per_px: float = 0.5):
    """Texto ficticio de `chars` caracteres: ancho por carácter y alto de línea ∝ fuente."""

    def measure(width, font_px):
        cw = char_w_per_px * font_px
        per_line = max(1, int(width // cw))
        lines = -(-chars // per_line)
        ideal = min(width, chars * cw)
        return ideal, lines * line_h_per_px * font_px

    return measure


def test_short_answer_gives_narrow_band():
    style = OverlayStyle()
    fit = fit_layout(fake_measure(20), SCREEN_W, SCREEN_H, style, header_h=20, header_w=150)
    assert not fit.truncated and fit.font_px == style.font_px
    assert fit.width < SCREEN_W * style.max_width
    assert fit.width >= style.min_width_px
    assert fit.height < 150


def test_medium_answer_grows_but_stays_within_max_width():
    style = OverlayStyle()
    fit = fit_layout(fake_measure(800), SCREEN_W, SCREEN_H, style, header_h=20)
    assert not fit.truncated and fit.font_px == style.font_px
    assert fit.width == int(SCREEN_W * style.max_width)
    assert fit.height <= SCREEN_H * style.max_height


def test_long_answer_widens_before_shrinking_font():
    style = OverlayStyle()
    # Cabe a 95 % pero no a 70 % con la letra base.
    chars = 2300
    fit = fit_layout(fake_measure(chars), SCREEN_W, SCREEN_H, style, header_h=20)
    assert not fit.truncated
    assert fit.font_px == style.font_px
    assert fit.width == int(SCREEN_W * style.wide_width)


def test_very_long_answer_shrinks_font_then_truncates():
    style = OverlayStyle()
    fit = fit_layout(fake_measure(4000), SCREEN_W, SCREEN_H, style, header_h=20)
    assert not fit.truncated and fit.font_px < style.font_px
    assert fit.font_px >= round(style.font_px * style.min_font_ratio)

    fit = fit_layout(fake_measure(60000), SCREEN_W, SCREEN_H, style, header_h=20)
    assert fit.truncated
    assert fit.height == int(SCREEN_H * style.max_height)
    assert fit.font_px == round(style.font_px * style.min_font_ratio)


def test_header_width_is_respected_for_tiny_answers():
    style = OverlayStyle(min_width_px=100)
    fit = fit_layout(fake_measure(2), SCREEN_W, SCREEN_H, style, header_h=20, header_w=600)
    assert fit.width == 600 + 2 * PAD_X


def test_compact_markdown_turns_headings_into_bold():
    assert compact_markdown("## Definición\ntexto\n# Otra #") == "**Definición**\ntexto\n**Otra**"


# --------------------------------------------------------------------------- ventana real (offscreen)


@pytest.fixture
def overlay(qapp):
    settings = default_settings()
    o = OverlayWindow(lambda: settings)
    yield o, settings
    o.hide_overlay()
    o.deleteLater()


def test_window_flags_make_it_click_through_and_focusless(overlay):
    from PySide6.QtCore import Qt

    o, _ = overlay
    flags = o.windowFlags()
    for f in (Qt.WindowType.WindowTransparentForInput, Qt.WindowType.WindowDoesNotAcceptFocus,
              Qt.WindowType.WindowStaysOnTopHint, Qt.WindowType.FramelessWindowHint, Qt.WindowType.Tool):
        assert flags & f
    assert o.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)


def test_window_fits_real_text_sizes(overlay, qapp):
    o, settings = overlay
    screen_h = qapp.primaryScreen().geometry().height()
    screen_w = qapp.primaryScreen().geometry().width()
    max_h = int(screen_h * settings.overlay.max_height)

    o.show_message("Dudas · gemini-4-hydrogen", "Sí.")
    short = o.last_fit()
    assert not short.truncated and short.height < 140
    assert o.height() == short.height and o.width() == short.width

    eight = "\n".join(f"- Punto {i}: explicación breve y al grano." for i in range(8))
    o.show_message("Dudas", eight)
    mid = o.last_fit()
    assert not mid.truncated and short.height < mid.height <= max_h
    assert mid.font_px == settings.overlay.font_px

    huge = " ".join(["palabra"] * 6000)
    o.show_message("Dudas", huge)
    big = o.last_fit()
    assert big.truncated and big.height == max_h
    assert big.width == min(screen_w, int(screen_w * settings.overlay.wide_width))
    # La franja queda centrada en vertical.
    centre = o.y() + o.height() / 2
    assert abs(centre - screen_h * settings.overlay.vertical_center) <= 1


def test_streaming_relayout_and_paint(overlay, qapp):
    o, _ = overlay
    o.begin("Dudas · gemini-4-hydrogen")
    assert o.is_shown()
    o.set_body("Hola")
    o.set_body("Hola **mundo** " * 30)
    qapp.processEvents()
    o._relayout()
    img = o.grab()  # fuerza paintEvent
    assert not img.isNull()
    o.finish("Dudas · gemini-4-hydrogen · 1,2 s")
    assert o.body_text().startswith("Hola")
    assert PAD_Y > 0
