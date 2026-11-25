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
