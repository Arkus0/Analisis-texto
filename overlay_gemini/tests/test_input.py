from app.config import Binding, default_settings
from app.input.bindings import InputEvent, keyboard_event, matches, vk_name
from app.input.hub import InputHub
from app.input.mouse_kb import (
    WM_KEYDOWN,
    WM_KEYUP,
    WM_XBUTTONDOWN,
    WM_XBUTTONUP,
    decode_key_msg,
    decode_mouse_msg,
)


def test_decode_mouse_side_buttons():
    ev = decode_mouse_msg(WM_XBUTTONDOWN, 1 << 16)
    assert ev == InputEvent("mouse", "x1", True, ev.label) and "X1" in ev.label
    assert decode_mouse_msg(WM_XBUTTONUP, 2 << 16).code == "x2"
    assert decode_mouse_msg(WM_XBUTTONUP, 2 << 16).pressed is False
    assert decode_mouse_msg(0x0201, 0) is None  # WM_LBUTTONDOWN: el clic izquierdo nunca se usa


def test_decode_keys_and_names():
    ev = decode_key_msg(WM_KEYDOWN, 0x78)
    assert ev.code == "vk:120" and ev.pressed and ev.label == "Tecla: F9"
    assert decode_key_msg(WM_KEYUP, 0x41).pressed is False
    assert vk_name(0x87) == "F24" and vk_name(0x13) == "Pausa" and vk_name(0xE9).startswith("VK")


def test_matches():
    b = Binding("gamepad", "a", "Mando: A")
    assert matches(b, InputEvent("gamepad", "a", True))
    assert not matches(b, InputEvent("gamepad", "b", True))
    assert not matches(b, InputEvent("joystick", "a", True))
    assert not matches(None, InputEvent("gamepad", "a", True))


def _hub(settings):
    hub = InputHub(lambda: settings)  # no se arranca: solo probamos el enrutado
    events = []
    hub.capture_pressed.connect(lambda: events.append("down"))
    hub.capture_released.connect(lambda: events.append("up"))
    hub.learned.connect(lambda b: events.append(b))
    hub.learn_cancelled.connect(lambda: events.append("cancel"))
    return hub, events


def test_hub_routes_bound_button(qapp):
    s = default_settings()
    s.capture_binding = Binding("gamepad", "a", "Mando: A")
    hub, events = _hub(s)
    hub.raw_event.emit(InputEvent("gamepad", "b", True))
    hub.raw_event.emit(InputEvent("gamepad", "a", True))
    hub.raw_event.emit(InputEvent("gamepad", "a", False))
    qapp.processEvents()
    assert events == ["down", "up"]


def test_hub_learning_and_escape(qapp):
    s = default_settings()
    hub, events = _hub(s)
    hub.begin_learn()
    hub.raw_event.emit(InputEvent("gamepad", "rightshoulder", False))  # las sueltas no cuentan
    hub.raw_event.emit(InputEvent("gamepad", "rightshoulder", True, "Mando: R"))
    qapp.processEvents()
    assert events == [Binding("gamepad", "rightshoulder", "Mando: R")] and not hub.learning

    events.clear()
    hub.begin_learn()
    hub.raw_event.emit(keyboard_event(0x1B, True))
    qapp.processEvents()
    assert events == ["cancel"]


# --------------------------------------------------------------------------- hooks bajo demanda


class FakeGamepad:
    def __init__(self, emit):
        self.started = 0

    def start(self):
        self.started += 1
        return None

    def stop(self):
        pass


class FakeMouseKb:
    def __init__(self, emit, binding, learning):
        self.running = False
        self.starts = 0
        self.stops = 0

    def start(self):
        self.running = True
        self.starts += 1
        return []

    def stop(self):
        self.running = False
        self.stops += 1


def _hub_with_fakes(settings):
    return InputHub(lambda: settings, gamepad_factory=FakeGamepad, mouse_kb_factory=FakeMouseKb)


def test_no_global_hooks_with_gamepad_binding(qapp):
    s = default_settings()
    s.capture_binding = Binding("gamepad", "a", "Mando: A")
    hub = _hub_with_fakes(s)
    hub.start()
    assert hub.gamepad.started == 1
    assert not hub.mouse_kb.running and hub.mouse_kb.starts == 0


def test_no_hooks_without_binding_either(qapp):
    hub = _hub_with_fakes(default_settings())
    hub.start()
    assert hub.mouse_kb.starts == 0


def test_hooks_only_for_mouse_or_keyboard_and_removed_when_switching(qapp):
    s = default_settings()
    s.capture_binding = Binding("mouse", "x1", "X1")
    hub = _hub_with_fakes(s)
    hub.start()
    assert hub.mouse_kb.running
    s.capture_binding = Binding("gamepad", "a")
    hub.sync_hooks()
    assert not hub.mouse_kb.running and hub.mouse_kb.stops == 1


def test_hooks_are_temporary_while_learning(qapp):
    s = default_settings()
    s.capture_binding = Binding("gamepad", "a")
    hub = _hub_with_fakes(s)
    hub.start()
    hub.begin_learn()
    assert hub.mouse_kb.running  # para poder asignar ratón/teclado
    hub.raw_event.emit(InputEvent("gamepad", "b", True, "Mando: B"))
    qapp.processEvents()
    assert not hub.learning and not hub.mouse_kb.running  # se quitan al terminar
    hub.begin_learn()
    hub.cancel_learn()
    assert not hub.mouse_kb.running
