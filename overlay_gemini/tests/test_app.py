"""La app completa no debe lanzar NINGÚN aviso, notificación ni ventana emergente."""

import pytest

from app.config import Binding, default_settings, save_settings


@pytest.fixture
def no_popups(monkeypatch):
    from PySide6.QtWidgets import QMessageBox, QSystemTrayIcon

    popups = []
    monkeypatch.setattr(QSystemTrayIcon, "showMessage", lambda *a, **k: popups.append(("tray", a)))
    for name in ("information", "warning", "critical", "question"):
        monkeypatch.setattr(QMessageBox, name, staticmethod(lambda *a, **k: popups.append((name, a))))
    return popups


@pytest.fixture
def configured(monkeypatch):
    s = default_settings()
    s.capture_binding = Binding("gamepad", "a", "Mando: A")
    save_settings(s)
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    # Sin red en los tests: el precalentamiento devuelve OK al instante.
    monkeypatch.setattr("app.gemini_client.GeminiService.warm_up", lambda self, key, model: "")
    return s


def _wait(qapp, ms):
    from PySide6.QtCore import QElapsedTimer

    t = QElapsedTimer()
    t.start()
    while t.elapsed() < ms:
        qapp.processEvents()


def test_startup_is_silent_and_without_hooks(qapp, no_popups, configured):
    import main

    app = main.App()
    try:
        _wait(qapp, 500)
        assert no_popups == []
        assert app.settings_window is None  # configurado: no se abre nada solo
        assert not app.hub.mouse_kb.running  # con mando: sin hooks globales
        assert app.api_status.startswith("✔")
    finally:
        app.quit()


def test_impact_test_runs_full_cycle_silently(qapp, no_popups, configured, monkeypatch):
    import main
    from app.controller import IDLE, SHOWING, WAITING

    monkeypatch.setattr(main, "SIM_DELAY_S", 0.2)
    app = main.App()
    try:
        app.start_impact_test()
        assert app.controller.state == WAITING and app.icon.is_shown()
        _wait(qapp, 700)
        assert app.controller.state == SHOWING and app.band.is_shown()
        assert "Base reguladora" in app.band.body_text()
        app.stop_impact_test()
        assert app.controller.state == IDLE
        assert app.controller.backend[0] is app.gemini  # se restaura el backend real
        assert no_popups == []
    finally:
        app.quit()


# --------------------------------------------------------------------------- conexión preparada


def test_keepalive_timer_runs_every_150_s(qapp, no_popups, configured):
    import main

    app = main.App()
    try:
        assert app._keepalive.isActive() and app._keepalive.interval() == main.KEEPALIVE_S * 1000
    finally:
        app.quit()


def test_keepalive_only_when_idle_and_with_key(qapp, no_popups, configured, monkeypatch):
    import time

    import main

    app = main.App()
    try:
        calls = []
        monkeypatch.setattr(app, "warm_up", lambda: calls.append(1))
        app.gemini.last_activity = time.monotonic()  # tráfico reciente
        app._keepalive_tick()
        assert calls == []
        app.gemini.last_activity = time.monotonic() - main.KEEPALIVE_S  # inactivo
        app._keepalive_tick()
        assert calls == [1]
    finally:
        app.quit()


def test_keepalive_skipped_without_key(qapp, no_popups, configured, monkeypatch):
    import main

    app = main.App()
    try:
        calls = []
        monkeypatch.setattr(app, "warm_up", lambda: calls.append(1))
        monkeypatch.setattr("app.config.get_api_key", lambda: "")
        app.gemini.last_activity = 0.0
        app._keepalive_tick()
        assert calls == []
    finally:
        app.quit()


def test_warm_up_updates_last_activity_without_generating():
    from types import SimpleNamespace as NS

    from app.gemini_client import GeminiService

    asked = []
    client = NS(models=NS(get=lambda model: asked.append(model)),
                interactions=NS(create=lambda **kw: pytest.fail("no debe generar texto")))
    svc = GeminiService(lambda key: client)
    assert svc.last_activity == 0.0
    assert svc.warm_up("k", "models/gemini-4-hydrogen") == ""
    assert asked == ["gemini-4-hydrogen"] and svc.last_activity > 0


# --------------------------------------------------------------------------- arrancar con Windows


def test_autostart_never_opens_settings_even_if_unconfigured(qapp, no_popups, monkeypatch):
    import main

    monkeypatch.setattr("app.gemini_client.GeminiService.warm_up", lambda self, key, model: "")
    app = main.App(from_autostart=True)  # sin API key ni botón
    try:
        _wait(qapp, 500)
        assert app.settings_window is None and no_popups == []
    finally:
        app.quit()


def test_normal_start_unconfigured_opens_settings(qapp, no_popups, monkeypatch):
    import main

    monkeypatch.setattr("app.gemini_client.GeminiService.warm_up", lambda self, key, model: "")
    app = main.App()
    try:
        _wait(qapp, 500)
        assert app.settings_window is not None
    finally:
        if app.settings_window is not None:
            app.settings_window.reject()
        app.quit()


def test_settings_checkbox_applies_autostart_on_save(qapp, configured, monkeypatch):
    from app import autostart
    from app.gemini_client import GeminiService
    from app.input.hub import InputHub
    from app.settings_window import SettingsWindow

    calls = []
    monkeypatch.setattr(autostart, "supported", lambda: True)
    monkeypatch.setattr(autostart, "is_enabled", lambda *a, **k: False)
    monkeypatch.setattr(autostart, "set_enabled", lambda on, *a, **k: calls.append(on) or True)
    s = configured
    hub = InputHub(lambda: s)
    w = SettingsWindow(s, hub, GeminiService(), True)
    try:
        assert w.autostart.isEnabled() and not w.autostart.isChecked()
        assert w._do_save() and calls == []  # sin cambios: no toca el registro
        w.autostart.setChecked(True)
        assert w._do_save() and calls == [True]
    finally:
        w.reject()
        hub.stop()
