import pytest

from app.config import default_settings
from app.controller import IDLE, SHOWING, WAITING, Controller
from app.gemini_client import Citation, StreamPiece, Timing


class FakeBand:
    def __init__(self):
        self.shown = False
        self.answer = None
        self.calls = []

    def is_shown(self):
        return self.shown

    def has_content(self):
        return self.answer is not None

    def show_answer(self, header, markdown, citations=None, error=False):
        self.calls.append("show")
        self.answer = dict(header=header, text=markdown, citations=citations, error=error)
        self.shown = True

    def fade_out(self, ms=None):
        self.calls.append("fade_out")
        self.shown = False

    def hide_now(self):
        self.shown = False


class FakeIcon:
    def __init__(self):
        self.shown = False
        self.error = False
        self.calls = []

    def start(self):
        self.calls.append("start")
        self.shown, self.error = True, False

    def flash_error(self, hold_ms=2000):
        self.calls.append("error")
        self.shown, self.error = True, True

    def fade_out(self, ms=None):
        self.calls.append("fade_out")
        self.shown = False

    def hide_now(self):
        self.shown = False

    def is_shown(self):
        return self.shown


class FakeGemini:
    """Guarda los callbacks para dispararlos a mano (como si fueran del hilo)."""

    def __init__(self):
        self.requests = []

    def start(self, key, request, on_piece, on_done, on_error):
        built = request() if callable(request) else request
        self.requests.append(dict(request=built, piece=on_piece, done=on_done, error=on_error))


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class Env:
    def __init__(self, qapp, api_key="key", grab=None):
        self.qapp = qapp
        self.settings = default_settings()
        self.band, self.icon, self.gemini, self.clock = FakeBand(), FakeIcon(), FakeGemini(), Clock()
        self.grabs, self.prepared = [], []

        def default_grab(s):
            self.grabs.append(s)
            return "IMAGEN"

        def prepare(img, s):
            self.prepared.append(img)
            return b"jpeg"

        self.c = Controller(self.band, self.icon, lambda: self.settings, grab or default_grab, prepare,
                            self.gemini, api_key_provider=lambda: api_key, clock=self.clock)

    def tap(self, held=0.1, gap=1.0):
        self.clock.t += gap
        self.c.press()
        self.clock.t += held
        self.c.release()
        self.qapp.processEvents()

    def last(self):
        return self.gemini.requests[-1]


@pytest.fixture
def env(qapp):
    return Env(qapp)


def test_press_shows_icon_then_band_when_complete(env):
    env.tap()
    assert env.c.state == WAITING
    assert env.icon.shown and not env.band.shown
    assert env.grabs and env.prepared == ["IMAGEN"]  # imagen preparada en el "hilo" de la petición
    r = env.last()
    r["piece"](StreamPiece(text="Hola "))
    r["piece"](StreamPiece(text="mundo"))
    assert not env.band.shown  # nada de streaming en pantalla: solo al terminar
    env.clock.t += 2.4
    r["done"](Timing(total=2.4, first_text=0.9))
    env.qapp.processEvents()
    assert env.c.state == SHOWING
    assert env.band.shown and not env.icon.shown
    assert env.band.answer["text"] == "Hola mundo"
    assert env.band.answer["header"].startswith("Dudas · gemini-4-hydrogen · 2,4 s")


def test_second_press_hides_with_fade(env):
    env.tap()
    env.last()["done"](None)
    env.tap()
    assert env.c.state == IDLE and env.band.calls[-1] == "fade_out"
    env.tap()
    assert env.c.state == WAITING and len(env.gemini.requests) == 2


def test_cancel_while_waiting_never_pops_up_later(env):
    env.tap()
    r = env.last()
    env.tap()  # cancelar la espera
    assert env.c.state == IDLE and not env.icon.shown
    r["piece"](StreamPiece(text="tardía"))
    r["done"](None)
    env.qapp.processEvents()
    assert not env.band.shown and env.band.calls == []  # no aparece sola
    env.tap(held=0.8)  # pulsación larga: ahora sí
    assert env.band.shown and env.band.answer["text"] == "tardía"
    assert len(env.gemini.requests) == 1


def test_long_press_while_pending_shows_icon_again_and_then_band(env):
    env.tap()
    r = env.last()
    env.tap()  # cancelar
    env.tap(held=0.8)  # larga: la respuesta aún no ha llegado
    assert env.c.state == WAITING and env.icon.shown
    r["done"](None)
    env.qapp.processEvents()
    assert env.c.state == SHOWING and env.band.shown


def test_error_turns_icon_red_without_band(env):
    env.tap()
    env.last()["error"]("Cuota agotada (429)")
    env.qapp.processEvents()
    assert env.c.state == IDLE
    assert env.icon.error and env.icon.calls[-1] == "error"
    assert not env.band.shown and env.band.calls == []
    env.tap(held=0.8)  # el error se puede leer con una pulsación larga
    assert env.band.answer["error"] and "429" in env.band.answer["text"]


def test_error_after_cancel_is_silent(env):
    env.tap()
    r = env.last()
    env.tap()
    r["error"]("falló")
    env.qapp.processEvents()
    assert "error" not in env.icon.calls and not env.band.shown
    assert env.c.last.error


def test_timeout_turns_icon_red_and_discards_late_answer(env):
    env.settings.wait_timeout_s = 5
    env.tap()
    r = env.last()
    env.c._on_timeout()  # equivalente a que salte el QTimer
    assert env.c.state == IDLE and env.icon.error
    assert "no ha respondido" in env.c.last.text
    r["piece"](StreamPiece(text="tarde"))
    r["done"](None)
    env.qapp.processEvents()
    assert not env.band.shown


def test_stale_responses_are_ignored(env):
    env.tap()
    old = env.last()
    env.tap()  # cancelar
    env.tap()  # nueva captura
    new = env.last()
    old["piece"](StreamPiece(text="VIEJA"))
    old["done"](None)
    new["piece"](StreamPiece(text="nueva"))
    new["piece"](StreamPiece(citations=[Citation("https://boe.es", "boe.es")]))
    new["done"](None)
    env.qapp.processEvents()
    assert env.band.answer["text"] == "nueva"
    assert env.band.answer["citations"] == [Citation("https://boe.es", "boe.es")]


def test_debounce_and_autorepeat(env):
    env.tap()
    env.tap(gap=0.05)  # rebote
    assert env.c.state == WAITING
    env.c.press()
    env.clock.t += 0.3
    env.c.press()  # auto-repetición de teclado: se ignora
    env.clock.t += 0.4
    env.c.release()  # 0,7 s → larga
    assert env.c.state == WAITING and len(env.gemini.requests) == 1


def test_long_press_with_nothing_does_nothing(env):
    env.tap(held=0.8)
    assert env.c.state == IDLE and not env.band.shown and not env.icon.shown


def test_missing_api_key_flashes_red_icon_only(qapp):
    e = Env(qapp, api_key="")
    e.tap()
    assert e.icon.error and not e.band.shown and not e.grabs and not e.gemini.requests
    assert "API key" in e.c.last.text


def test_capture_failure_flashes_red_icon(qapp):
    def boom(s):
        raise RuntimeError("pantalla negra")

    e = Env(qapp, grab=boom)
    e.tap()
    assert e.icon.error and not e.gemini.requests and "pantalla negra" in e.c.last.text


def test_reset_hides_everything(env):
    env.tap()
    env.c.reset()
    assert env.c.state == IDLE and not env.icon.shown
    env.last()["done"](None)
    env.qapp.processEvents()
    assert not env.band.shown
