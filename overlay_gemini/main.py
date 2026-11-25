"""Overlay Gemini: pulsa un botón → captura → Gemini → franja sobre la pantalla.

Uso:
    python main.py              # arranca en la bandeja del sistema
    python main.py --settings   # abre Ajustes al arrancar
    python main.py --autostart  # como lo lanza Windows al iniciar sesión (solo bandeja)
    python main.py --selftest selftest.log   # comprobación sin interfaz (CI / .exe)

Diseñada para convivir con OBS: proceso aparte y de prioridad baja, sin GPU, sin
hooks globales si usas mando y sin ningún aviso, notificación ni ventana emergente.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import time
from logging.handlers import RotatingFileHandler

from PySide6.QtCore import QObject, Signal

log = logging.getLogger("overlay_gemini")

SAMPLE_TEXT = (
    "**Base reguladora**: cociente que resulta de dividir las bases de cotización del "
    "trabajador durante un período determinado entre el divisor que fija la ley.\n\n"
    "- Sirve para calcular la cuantía de la prestación.\n"
    "- Para la jubilación se toman las bases de los **últimos 25 años** (art. 209 LGSS)."
)

IMPACT_TOTAL_S = 180  # prueba de impacto: 3 minutos
IMPACT_CYCLE_S = 10  # una "pulsación" cada 10 s
IMPACT_HIDE_AT_S = 6  # y se oculta a los 6 s
SIM_DELAY_S = 2.0  # "respuesta" simulada a los 2 s
KEEPALIVE_S = 150  # mantener la conexión con Gemini abierta (sin gastar tokens)


def setup_logging() -> None:
    """Log a archivo (sin capturas ni respuestas) y nada de diálogos de error."""
    from app.config import config_dir

    log.setLevel(logging.INFO)
    try:
        d = config_dir()
        d.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(d / "overlay.log", maxBytes=1_000_000, backupCount=1, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        log.addHandler(handler)
    except OSError:
        log.addHandler(logging.NullHandler())

    def excepthook(exc_type, exc, tb):
        log.error("Excepción no controlada", exc_info=(exc_type, exc, tb))

    def thread_excepthook(args):
        name = args.thread.name if args.thread else "?"
        log.error("Excepción en el hilo %s", name, exc_info=(args.exc_type, args.exc_value, args.exc_traceback))

    sys.excepthook = excepthook
    threading.excepthook = thread_excepthook


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


class SimulatedGemini:
    """Backend falso para la prueba de impacto: mismo ciclo (captura, JPEG, icono,
    franja), sin red y sin gastar API."""

    def start(self, api_key, request, on_piece, on_done, on_error):
        from app.gemini_client import StreamPiece, Timing

        def run():
            t0 = time.perf_counter()
            try:
                if callable(request):
                    request()  # codifica la imagen igual que una petición real
            except Exception as e:  # noqa: BLE001
                on_error(str(e))
                return
            time.sleep(SIM_DELAY_S)
            on_piece(StreamPiece(text=SAMPLE_TEXT))
            on_done(Timing(total=time.perf_counter() - t0))

        t = threading.Thread(target=run, name="simulacion", daemon=True)
        t.start()
        return t


class App(QObject):
    warm_result = Signal(str)

    def __init__(self, open_settings: bool = False, from_autostart: bool = False):
        super().__init__()
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QAction
        from PySide6.QtWidgets import QMenu, QSystemTrayIcon

        from app import autostart, win32
        from app.capture import grab_image, prepare_image
        from app.config import get_api_key, load_settings
        from app.controller import Controller
        from app.gemini_client import GeminiService
        from app.input.hub import InputHub
        from app.overlay import BusyIcon, OverlayWindow

        self.low_priority = win32.set_low_priority()
        self.settings = load_settings()
        self.preview = None  # Settings temporales para la vista previa
        self.settings_window = None
        self.api_status = ""

        provider = lambda: self.preview or self.settings  # noqa: E731
        self.band = OverlayWindow(provider)
        self.icon = BusyIcon(provider)
        self.gemini = GeminiService()
        self.controller = Controller(
            self.band,
            self.icon,
            lambda: self.settings,
            grab=lambda s: grab_image(s.screen_name),
            prepare=lambda img, s: prepare_image(img, s.capture_region, s.max_image_width),
            gemini=self.gemini,
        )
        self.hub = InputHub(lambda: self.settings)
        self.hub.capture_pressed.connect(self.controller.press)
        self.hub.capture_released.connect(self.controller.release)
        for err in self.hub.start():
            log.warning("Entrada: %s", err)  # se ve en Ajustes, nunca como aviso

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._end_preview)

        self._impact_timer = QTimer(self)
        self._impact_timer.setInterval(1000)
        self._impact_timer.timeout.connect(self._impact_tick)
        self._impact_elapsed = 0
        self._impact_saved_backend = None

        # ---- bandeja (sin globos ni notificaciones)
        self.tray = QSystemTrayIcon(_make_icon(), self)
        menu = QMenu()
        self.act_info = QAction("", menu)
        self.act_info.setEnabled(False)
        menu.addAction(self.act_info)
        menu.addSeparator()
        for text, slot in (
            ("Capturar y preguntar ahora", lambda: QTimer.singleShot(350, self.controller.capture_and_ask)),
            ("Mostrar última respuesta", self.controller.show_last),
            ("Ocultar", self._hide_all),
        ):
            a = QAction(text, menu)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        self.act_impact = QAction("Prueba de impacto en OBS (3 min, sin gastar API)", menu)
        self.act_impact.triggered.connect(self.toggle_impact_test)
        menu.addAction(self.act_impact)
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

        self.warm_result.connect(self._on_warm_result)
        self.warm_up()
        # Conexión siempre preparada: cada 150 s, si no ha habido tráfico, una petición
        # de metadatos (no gasta tokens) para que la siguiente pulsación no pague el TLS.
        self._keepalive = QTimer(self)
        self._keepalive.setInterval(KEEPALIVE_S * 1000)
        self._keepalive.timeout.connect(self._keepalive_tick)
        self._keepalive.start()
        self._refresh_info()

        if getattr(sys, "frozen", False):
            try:
                if autostart.refresh_path():
                    log.info("Arranque con Windows: ruta del .exe actualizada")
            except Exception as e:  # noqa: BLE001
                log.warning("Arranque con Windows: %s", e)

        log.info("Arrancado%s · prioridad baja: %s · captura excluida: %s · hooks: %s",
                 " (con Windows)" if from_autostart else "", self.low_priority,
                 self.band.capture_excluded, self.hub.mouse_kb.running)

        needs_setup = not get_api_key() or self.settings.capture_binding is None
        if from_autostart:
            if needs_setup:
                log.info("Falta configuración: abre Ajustes desde la bandeja cuando quieras")
        elif open_settings or needs_setup:
            QTimer.singleShot(300, self.open_settings)

    # ----------------------------------------------------------------- conexión
    def warm_up(self) -> None:
        """Abre la conexión con Gemini en segundo plano y valida la clave (en silencio)."""
        from app.config import get_api_key

        key = get_api_key()
        if not key:
            self._on_warm_result("Falta la API key.")
            return
        model = self.settings.model_for(self.settings.active_preset())
        threading.Thread(target=lambda: self.warm_result.emit(self.gemini.warm_up(key, model)),
                         name="warm-up", daemon=True).start()

    def _keepalive_tick(self) -> None:
        from app.config import get_api_key

        if self._impact_timer.isActive() or not get_api_key():
            return
        if time.monotonic() - self.gemini.last_activity < KEEPALIVE_S - 5:
            return  # ha habido tráfico hace poco: la conexión sigue abierta
        self.warm_up()

    def _on_warm_result(self, error: str) -> None:
        status = f"✖ {error}" if error else "✔ Clave válida y conexión preparada"
        if status != self.api_status:  # el log solo apunta los cambios
            log.info("Conexión con Gemini: %s", status)
        self.api_status = status
        self._refresh_info()

    # ----------------------------------------------------------------- bandeja
    def _refresh_info(self) -> None:
        s = self.settings
        b = s.capture_binding.describe() if s.capture_binding else "sin botón asignado"
        text = f"{s.active_preset().name} · {s.model_for(s.active_preset())} · {b}"
        self.act_info.setText(text)
        tip = "Overlay Gemini\n" + text + (f"\n{self.api_status}" if self.api_status else "")
        if self._impact_timer.isActive():
            tip += f"\nPrueba de impacto: {IMPACT_TOTAL_S - self._impact_elapsed} s restantes"
        self.tray.setToolTip(tip)

    def _on_tray_activated(self, reason) -> None:
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.open_settings()

    def _hide_all(self) -> None:
        from app.controller import SHOWING, WAITING

        if self.controller.state == SHOWING:
            self.controller.hide_answer()
        elif self.controller.state == WAITING:
            self.controller.cancel_wait()

    # ----------------------------------------------------------------- prueba de impacto
    def toggle_impact_test(self) -> None:
        if self._impact_timer.isActive():
            self.stop_impact_test()
        else:
            self.start_impact_test()

    def start_impact_test(self) -> None:
        self._impact_saved_backend = self.controller.backend
        self.controller.set_backend(SimulatedGemini(), lambda: "simulacion")
        self.controller.reset()
        self._impact_elapsed = 0
        self._impact_timer.start()
        self.act_impact.setText("Detener prueba de impacto")
        log.info("Prueba de impacto: inicio")
        self._impact_tick(first=True)

    def stop_impact_test(self) -> None:
        self._impact_timer.stop()
        if self._impact_saved_backend is not None:
            self.controller.set_backend(*self._impact_saved_backend)
            self._impact_saved_backend = None
        self.controller.reset()
        self.act_impact.setText("Prueba de impacto en OBS (3 min, sin gastar API)")
        self._refresh_info()
        log.info("Prueba de impacto: fin")

    def _impact_tick(self, first: bool = False) -> None:
        from app.controller import IDLE

        if not first:
            self._impact_elapsed += 1
        if self._impact_elapsed >= IMPACT_TOTAL_S:
            self.stop_impact_test()
            return
        phase = self._impact_elapsed % IMPACT_CYCLE_S
        if phase == 0 and self.controller.state == IDLE:
            self.controller.toggle()  # captura + icono + "respuesta" a los 2 s
        elif phase == IMPACT_HIDE_AT_S and self.controller.state != IDLE:
            self.controller.toggle()  # ocultar
        if phase == 0:
            self._refresh_info()

    # ----------------------------------------------------------------- ajustes
    def open_settings(self) -> None:
        from app.settings_window import SettingsWindow

        if self.settings_window is not None:
            self.settings_window.raise_()
            self.settings_window.activateWindow()
            return
        w = SettingsWindow(self.settings, self.hub, self.gemini, self.band.capture_excluded,
                           api_status=self.api_status)
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
        self.band.apply_native()
        self.icon.apply_native()
        self.hub.sync_hooks()
        self._refresh_info()
        self.warm_up()

    def _on_save_and_test(self) -> None:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(450, self.controller.capture_and_ask)

    def _on_preview(self, settings) -> None:
        from PySide6.QtCore import QTimer

        p = settings.active_preset()
        self.preview = settings
        self.controller.reset()
        self.icon.start()

        def show_band():
            if self.preview is None:
                return
            self.icon.fade_out()
            self.band.show_message(f"Vista previa · {p.name} · {settings.model_for(p)}", SAMPLE_TEXT)

        QTimer.singleShot(1200, show_band)
        self._preview_timer.start(6000)

    def _end_preview(self) -> None:
        if self.preview is not None:
            self.band.fade_out()
            self.icon.hide_now()
            self.preview = None

    def quit(self) -> None:
        from PySide6.QtWidgets import QApplication

        if self._impact_timer.isActive():
            self.stop_impact_test()
        self.hub.stop()
        self.tray.hide()
        log.info("Cerrado")
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
        from app.overlay import BusyIcon, OverlayWindow

        s = default_settings()
        o = OverlayWindow(lambda: s)
        o.show_message("Selftest", SAMPLE_TEXT)
        fit = o.last_fit()
        o.hide_now()
        icon = BusyIcon(lambda: s)
        icon.start()
        icon.flash_error(10)
        icon.hide_now()
        return f"franja {fit.width}×{fit.height}px, letra {fit.font_px}px; icono OK"

    def _priority():
        from app import win32

        if sys.platform != "win32":
            return "no aplica fuera de Windows"
        if not win32.set_low_priority():
            raise RuntimeError("SetPriorityClass ha fallado")
        return "por debajo de lo normal"

    def _jpeg():
        from app.capture import encode_image

        img = QImage(64, 64, QImage.Format.Format_RGB32)
        img.fill(QColor("#336699"))
        return f"{len(encode_image(img))} bytes JPEG"

    for name, fn in (("config", _config), ("sdl2", _sdl), ("pynput", _pynput), ("keyring", _keyring),
                     ("google-genai", _genai), ("overlay", _overlay), ("jpeg", _jpeg),
                     ("prioridad", _priority)):
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
    parser.add_argument("--autostart", action="store_true",
                        help="arranque con Windows: solo bandeja, nunca abre ventanas")
    parser.add_argument("--selftest", nargs="?", const="", metavar="LOG",
                        help="comprobar dependencias y salir")
    args = parser.parse_args(argv)

    if args.selftest is not None:
        return selftest(args.selftest or None)

    from PySide6.QtCore import QDir, QLockFile
    from PySide6.QtWidgets import QApplication

    setup_logging()
    qapp = QApplication(sys.argv)
    qapp.setApplicationName("Overlay Gemini")
    qapp.setQuitOnLastWindowClosed(False)

    lock = QLockFile(os.path.join(QDir.tempPath(), "overlay-gemini.lock"))
    if not lock.tryLock(200):
        log.info("Ya había una instancia abierta: se sale en silencio")
        return 0

    app = App(open_settings=args.settings, from_autostart=args.autostart)  # noqa: F841 - mantiene vivos los objetos
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
