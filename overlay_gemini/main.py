"""Overlay Gemini: pulsa un botón → captura → Gemini → franja sobre la pantalla.

Uso:
    python main.py              # arranca en la bandeja del sistema
    python main.py --settings   # abre Ajustes al arrancar
    python main.py --selftest selftest.log   # comprobación sin interfaz (CI / .exe)
"""

from __future__ import annotations

import argparse
import os
import sys


SAMPLE_TEXT = (
    "**Base reguladora**: cociente que resulta de dividir las bases de cotización del "
    "trabajador durante un período determinado entre el divisor que fija la ley.\n\n"
    "- Sirve para calcular la cuantía de la prestación.\n"
    "- Para la jubilación se toman las bases de los **últimos 25 años** (art. 209 LGSS)."
)


def _make_icon():
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap

    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, 64, 64)
    grad.setColorAt(0, QColor("#4f8cff"))
    grad.setColorAt(1, QColor("#a35cff"))
    p.setBrush(QBrush(grad))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(4, 4, 56, 56), 14, 14)
    p.setBrush(QColor(255, 255, 255, 230))
    p.drawRoundedRect(QRectF(12, 27, 40, 10), 5, 5)  # la franja
    f = QFont("Segoe UI")
    f.setPixelSize(15)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 6, 64, 20), Qt.AlignmentFlag.AlignCenter, "G")
    p.end()
    return QIcon(pm)


class App:
    def __init__(self, open_settings: bool = False):
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu, QSystemTrayIcon

        from app.capture import grab_screen
        from app.config import get_api_key, load_settings
        from app.controller import Controller
        from app.gemini_client import GeminiService
        from app.input.hub import InputHub
        from app.overlay import OverlayWindow

        self.settings = load_settings()
        self.preview = None  # Settings temporales para la vista previa
        self.settings_window = None

        self.overlay = OverlayWindow(lambda: self.preview or self.settings)
        self.gemini = GeminiService()
        self.controller = Controller(
            self.overlay,
            lambda: self.settings,
            capture=lambda s: grab_screen(s.screen_name, s.max_image_width),
            gemini=self.gemini,
        )
        self.hub = InputHub(lambda: self.settings)
        self.hub.capture_pressed.connect(self.controller.press)
        self.hub.capture_released.connect(self.controller.release)
        input_errors = self.hub.start()

        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._end_preview)

        # ---- bandeja
        self.tray = QSystemTrayIcon(_make_icon())
        menu = QMenu()
        self.act_info = QAction("")
        self.act_info.setEnabled(False)
        menu.addAction(self.act_info)
        menu.addSeparator()
        for text, slot in (
            ("Capturar y preguntar ahora", lambda: QTimer.singleShot(350, self.controller.capture_and_ask)),
            ("Mostrar última respuesta", self.controller.show_last),
            ("Ocultar franja", self.overlay.hide_overlay),
        ):
            a = QAction(text, menu)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        a = QAction("Ajustes…", menu)
        a.triggered.connect(self.open_settings)
        menu.addAction(a)
        a = QAction("Salir", menu)
        a.triggered.connect(self.quit)
        menu.addAction(a)
        self._menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()
        self._refresh_info()

        if input_errors:
            self.tray.showMessage("Overlay Gemini", "Aviso de entrada: " + " · ".join(input_errors),
                                  QSystemTrayIcon.MessageIcon.Warning, 6000)
        if open_settings or not get_api_key() or self.settings.capture_binding is None:
            QTimer.singleShot(300, self.open_settings)
        else:
            self.tray.showMessage(
                "Overlay Gemini listo",
                f"Botón: {self.settings.capture_binding.describe()} · Prompt: {self.settings.active_preset().name}",
                QSystemTrayIcon.MessageIcon.Information, 3500)

    # ----------------------------------------------------------------- bandeja
    def _refresh_info(self) -> None:
        s = self.settings
        b = s.capture_binding.describe() if s.capture_binding else "sin botón asignado"
        text = f"{s.active_preset().name} · {s.model_for(s.active_preset())} · {b}"
        self.act_info.setText(text)
        self.tray.setToolTip("Overlay Gemini\n" + text)

    def _on_tray_activated(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_settings()

    # ----------------------------------------------------------------- ajustes
    def open_settings(self) -> None:
        from app.settings_window import SettingsWindow

        if self.settings_window is not None:
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        w = SettingsWindow(self.settings, self.hub, self.gemini, self.overlay.capture_excluded)
        w.saved.connect(self._on_saved)
        w.save_and_test.connect(self._on_save_and_test)
        w.preview_requested.connect(self._on_preview)
        w.finished.connect(self._on_settings_closed)
        self.settings_window = w
        w.show()
        w.raise_()
        w.activateWindow()

    def _on_settings_closed(self, _result: int) -> None:
        if self.settings_window is not None:
            self.settings_window.deleteLater()
        self.settings_window = None
        self._end_preview()

    def _on_saved(self, settings, _key: str) -> None:
        from app.config import save_settings

        self.settings = settings
        save_settings(settings)
        self.overlay.apply_native()
        self._refresh_info()

    def _on_save_and_test(self) -> None:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(450, self.controller.capture_and_ask)

    def _on_preview(self, settings) -> None:
        p = settings.active_preset()
        self.preview = settings
        self.overlay.show_message(f"Vista previa · {p.name} · {settings.model_for(p)}", SAMPLE_TEXT)
        self._preview_timer.start(5000)

    def _end_preview(self) -> None:
        if self.preview is not None:
            self.preview = None
            self.overlay.hide_overlay()

    def quit(self) -> None:
        from PySide6.QtWidgets import QApplication

        self.hub.stop()
        self.tray.hide()
        QApplication.quit()


# --------------------------------------------------------------------------- selftest


def selftest(log_path: str | None) -> int:
    """Comprueba que todas las piezas cargan (útil en CI y en el .exe empaquetado)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    lines: list[str] = []
    ok = True

    def check(name, fn):
        nonlocal ok
        try:
            lines.append(f"OK   {name}: {fn()}")
        except Exception as e:  # noqa: BLE001
            ok = False
            lines.append(f"FAIL {name}: {e!r}")

    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication

    qapp = QApplication.instance() or QApplication([])

    def _config():
        from app.config import default_settings, settings_from_dict, settings_to_dict

        s = settings_from_dict(settings_to_dict(default_settings()))
        return f"{len(s.presets)} prompts, modelo {s.model}"

    def _sdl():
        import sdl2

        v = sdl2.SDL_version()
        sdl2.SDL_GetVersion(v)
        return f"SDL {v.major}.{v.minor}.{v.patch}"

    def _pynput():
        if sys.platform != "win32" and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            return "omitido (sin pantalla gráfica en este sistema)"
        from pynput import keyboard, mouse

        return f"{keyboard.Listener.__module__}, {mouse.Listener.__module__}"

    def _keyring():
        import keyring

        return keyring.get_keyring().__class__.__name__

    def _genai():
        from google import genai

        from app.config import default_settings
        from app.gemini_client import build_request

        client = genai.Client(api_key="selftest")
        _ = client.interactions.create  # fuerza la carga perezosa del módulo
        from google.genai._gaos.types.interactions import CreateModelInteraction

        s = default_settings()
        req = build_request(s.active_preset(), s, b"\x89PNG\r\n\x1a\n")
        req.pop("stream", None)
        CreateModelInteraction.model_validate(req)
        return f"google-genai {genai.__version__}, petición válida para {req['model']}"

    def _overlay():
        from app.config import default_settings
        from app.overlay import OverlayWindow

        s = default_settings()
        o = OverlayWindow(lambda: s)
        o.show_message("Selftest", SAMPLE_TEXT)
        fit = o.last_fit()
        o.hide_overlay()
        return f"franja {fit.width}×{fit.height}px, letra {fit.font_px}px"

    def _jpeg():
        from app.capture import encode_image

        img = QImage(64, 64, QImage.Format.Format_RGB32)
        img.fill(QColor("#336699"))
        return f"{len(encode_image(img))} bytes JPEG"

    for name, fn in (("config", _config), ("sdl2", _sdl), ("pynput", _pynput), ("keyring", _keyring),
                     ("google-genai", _genai), ("overlay", _overlay), ("jpeg", _jpeg)):
        check(name, fn)
    del qapp

    report = "\n".join(lines) + f"\n{'SELFTEST OK' if ok else 'SELFTEST FAILED'}\n"
    if log_path:
        with open(log_path, "w", encoding="utf-8") as fh:
            fh.write(report)
    try:
        sys.stdout.write(report)
    except Exception:  # noqa: BLE001 - en el .exe sin consola no hay stdout
        pass
    return 0 if ok else 1


# --------------------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Overlay Gemini")
    parser.add_argument("--settings", action="store_true", help="abrir Ajustes al arrancar")
    parser.add_argument("--selftest", nargs="?", const="", metavar="LOG",
                        help="comprobar dependencias y salir")
    args = parser.parse_args(argv)

    if args.selftest is not None:
        return selftest(args.selftest or None)

    from PySide6.QtCore import QDir, QLockFile
    from PySide6.QtWidgets import QApplication, QMessageBox

    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Overlay Gemini")
    qapp.setQuitOnLastWindowClosed(False)

    lock = QLockFile(os.path.join(QDir.tempPath(), "overlay-gemini.lock"))
    if not lock.tryLock(200):
        QMessageBox.information(None, "Overlay Gemini", "Overlay Gemini ya está abierto (mira la bandeja del sistema).")
        return 0

    app = App(open_settings=args.settings)  # noqa: F841 - mantiene vivos los objetos
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
