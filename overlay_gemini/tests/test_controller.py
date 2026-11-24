import pytest

from app.config import default_settings
from app.controller import Controller
from app.gemini_client import Citation, StreamPiece


class FakeOverlay:
    def __init__(self):
        self.shown = False
        self.header = ""
        self.body = ""
        self.error = False
        self.citations = []
        self.calls = []

    def is_shown(self):
        return self.shown

    def has_content(self):
        return bool(self.header or self.body)

    def begin(self, header):
        self.calls.append("begin")
        self.header, self.body, self.error, self.shown = header, "", False, True

    def set_header(self, header):
        self.header = header

    def set_body(self, md):
        self.body = md

    def add_citations(self, c):
        self.citations += c

    def finish(self, header):
        self.calls.append("finish")
        self.header = header

    def show_message(self, header, message, error=False, show=True):
        self.calls.append("message")
        self.header, self.body, self.error = header, message, error
        if show:
            self.shown = True

    def show_overlay(self):
        self.calls.append("show")
        self.shown = True

    def hide_overlay(self):
        self.calls.append("hide")
        self.shown = False


class FakeGemini:
    """Guarda los callbacks para dispararlos a mano (como si fueran del hilo)."""

    def __init__(self):
        self.requests = []

    def start(self, key, request, on_piece, on_done, on_error):
        self.requests.append(dict(request=request, piece=on_piece, done=on_done, error=on_error))


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


@pytest.fixture
def env(qapp):
    settings = default_settings()
    overlay, gemini, clock = FakeOverlay(), FakeGemini(), Clock()
    captures = []

    def capture(s):
        captures.append(s)
        return b"jpeg"

    c = Controller(overlay, lambda: settings, capture, gemini, api_key_provider=lambda: "key", clock=clock)
    return NS(c=c, overlay=overlay, gemini=gemini, clock=clock, settings=settings, captures=captures, qapp=qapp)


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def tap(e, held=0.1, gap=1.0):
    e.clock.t += gap
    e.c.press()
    e.clock.t += held
    e.c.release()
    e.qapp.processEvents()


def test_toggle_cycle_capture_hide_capture(env):
    tap(env)
    assert env.overlay.shown and len(env.captures) == 1 and env.overlay.calls == ["begin"]
    assert env.overlay.header.startswith("Dudas · gemini-4-hydrogen")
    tap(env)
    assert not env.overlay.shown and len(env.captures) == 1
    tap(env)
    assert env.overlay.shown and len(env.captures) == 2


def test_streaming_updates_body_and_finishes_with_elapsed(env):
    tap(env)
    r = env.gemini.requests[-1]
    r["piece"](StreamPiece(text="Hola "))
    r["piece"](StreamPiece(text="mundo"))
    r["piece"](StreamPiece(citations=[Citation("https://boe.es", "boe.es")]))
    env.clock.t += 2.34
    r["done"]()
    env.qapp.processEvents()
    assert env.overlay.body == "Hola mundo"
    assert env.overlay.citations == [Citation("https://boe.es", "boe.es")]
    assert env.overlay.header.endswith("s") and "," in env.overlay.header


def test_stale_responses_are_ignored(env):
    tap(env)
    old = env.gemini.requests[-1]
    tap(env)  # oculta
    tap(env)  # nueva captura
    new = env.gemini.requests[-1]
    old["piece"](StreamPiece(text="VIEJA"))
    new["piece"](StreamPiece(text="nueva"))
    env.qapp.processEvents()
    assert env.overlay.body == "nueva"


def test_text_keeps_arriving_while_hidden_and_long_press_shows_it(env):
    tap(env)
    r = env.gemini.requests[-1]
    tap(env)  # ocultar antes de que llegue la respuesta
    r["piece"](StreamPiece(text="respuesta"))
    r["done"]()
    env.qapp.processEvents()
    assert not env.overlay.shown and env.overlay.body == "respuesta"
    tap(env, held=0.8)  # pulsación larga
    assert env.overlay.shown and len(env.captures) == 1  # sin nueva captura


def test_debounce_ignores_bounces(env):
    tap(env)
    tap(env, gap=0.05)  # rebote: < 250 ms desde la última acción
    assert env.overlay.shown


def test_keyboard_autorepeat_press_is_ignored(env):
    env.c.press()
    env.clock.t += 0.3
    env.c.press()  # auto-repetición
    env.clock.t += 0.4
    env.c.release()  # 0,7 s desde la primera pulsación → larga
    env.qapp.processEvents()
    assert env.overlay.calls == ["message"]  # "aún no hay respuesta"
    assert env.captures == []


def test_error_while_visible_is_shown_in_red(env):
    tap(env)
    env.gemini.requests[-1]["error"]("Cuota agotada (429)")
    env.qapp.processEvents()
    assert env.overlay.shown and env.overlay.error and "429" in env.overlay.body


def test_error_while_hidden_stays_hidden(env):
    tap(env)
    r = env.gemini.requests[-1]
    tap(env)
    r["error"]("falló")
    env.qapp.processEvents()
    assert not env.overlay.shown and env.overlay.error


def test_missing_api_key_shows_message_without_capturing(qapp):
    settings = default_settings()
    overlay, gemini = FakeOverlay(), FakeGemini()
    captured = []
    c = Controller(overlay, lambda: settings, lambda s: captured.append(1) or b"", gemini,
                   api_key_provider=lambda: "")
    c.capture_and_ask()
    assert overlay.error and "API key" in overlay.header and not captured and not gemini.requests


def test_capture_failure_is_reported(qapp):
    settings = default_settings()
    overlay, gemini = FakeOverlay(), FakeGemini()

    def boom(s):
        raise RuntimeError("pantalla negra")

    c = Controller(overlay, lambda: settings, boom, gemini, api_key_provider=lambda: "k")
    c.capture_and_ask()
    assert overlay.error and "pantalla negra" in overlay.body and not gemini.requests
