import pytest

from app.config import OverlayStyle, default_settings
from app.overlay import PAD_X, OverlayWindow, compact_markdown, fit_layout

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
    o.hide_now()
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
    # La pantalla virtual de los tests es pequeña (800×800) y las métricas de fuente
    # cambian según el SO: puede que haya tenido que reducir algo la letra, pero cabe.
    assert not mid.truncated and short.height < mid.height <= max_h
    assert mid.font_px >= round(settings.overlay.font_px * settings.overlay.min_font_ratio)

    settings.overlay.max_height = 0.9  # con sitio de sobra, se mantiene la letra base
    o.show_message("Dudas", eight)
    roomy = o.last_fit()
    assert not roomy.truncated and roomy.font_px == settings.overlay.font_px
    settings.overlay.max_height = 0.45

    huge = " ".join(["palabra"] * 6000)
    o.show_message("Dudas", huge)
    big = o.last_fit()
    assert big.truncated and big.height == max_h
    assert big.width == min(screen_w, int(screen_w * settings.overlay.wide_width))
    # La franja queda centrada en vertical.
    centre = o.y() + o.height() / 2
    assert abs(centre - screen_h * settings.overlay.vertical_center) <= 1


def _wait_anim(qapp, ms=600):
    from PySide6.QtCore import QElapsedTimer

    t = QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        qapp.processEvents()


def test_show_answer_lays_out_once_and_fades_in_and_out(overlay, qapp):
    o, settings = overlay
    calls = []
    original = o._relayout
    o._relayout = lambda: (calls.append(1), original())[1]
    o.show_answer("Dudas · gemini-4-hydrogen · 1,2 s", "Hola **mundo** " * 30)
    assert calls == [1]  # una sola maquetación
    assert o.is_shown() and o.windowOpacity() < 1.0  # empieza el fundido
    _wait_anim(qapp, settings.overlay.fade_ms + 250)
    assert o.windowOpacity() == pytest.approx(1.0)
    assert not o.grab().isNull()  # pinta sin errores
    o.fade_out()
    assert not o.is_shown()  # lógicamente oculta en cuanto empieza a desvanecerse
    _wait_anim(qapp, settings.overlay.fade_ms + 250)
    assert not o.isVisible()


def test_fade_zero_is_instant(overlay, qapp):
    o, settings = overlay
    settings.overlay.fade_ms = 0
    o.show_answer("x", "texto")
    assert o.isVisible() and o.windowOpacity() == pytest.approx(1.0)
    o.fade_out()
    assert not o.isVisible()


def test_fade_in_interrupts_fade_out(overlay, qapp):
    o, settings = overlay
    o.show_answer("x", "texto")
    _wait_anim(qapp, settings.overlay.fade_ms + 250)
    o.fade_out()
    o.reveal()  # pulsación larga a mitad del fundido de salida
    _wait_anim(qapp, settings.overlay.fade_ms + 250)
    assert o.isVisible() and o.is_shown()


def test_error_answer_paints(overlay):
    o, _ = overlay
    o.show_answer("Error · Dudas", "Cuota agotada (429)", error=True)
    assert not o.grab().isNull()


def test_busy_icon_spins_only_while_visible_and_flashes_red(qapp):
    from app.overlay import BusyIcon

    settings = default_settings()
    icon = BusyIcon(lambda: settings)
    icon.start()
    assert icon.is_shown() and icon._spin.isActive() and not icon.error
    geo = qapp.primaryScreen().geometry()
    centre = icon.geometry().center()
    assert abs(centre.x() - geo.center().x()) <= 1
    assert abs(centre.y() - geo.height() * settings.overlay.vertical_center) <= 1
    assert not icon.grab().isNull()
    icon.flash_error(hold_ms=50)
    assert icon.error and not icon._spin.isActive()
    assert not icon.grab().isNull()
    _wait_anim(qapp, 50 + settings.overlay.fade_ms + 300)
    assert not icon.isVisible() and not icon._spin.isActive()
    icon.deleteLater()
