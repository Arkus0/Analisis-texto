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
