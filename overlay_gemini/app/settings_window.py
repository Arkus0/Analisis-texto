"""Ventana de Ajustes: API key, modelo, prompts, botón, pantalla y aspecto."""

from __future__ import annotations

import copy
import threading

from PySide6.QtCore import QObject, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QAbstractItemView,
    QHeaderView,
    QListWidgetItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from . import autostart
from .capture import describe_screen, find_screen, grab_image, prepare_image
from .config import Preset, Settings, api_key_from_env, get_api_key, new_id, set_api_key
from .gemini_client import GeminiService, build_request, friendly_error
from .input.hub import InputHub
from .models import LEVEL_LABELS, RESOLUTIONS, SUGGESTED_MODELS, thinking_levels
from .region_picker import RegionPicker

LEARN_TIMEOUT_MS = 15000


class _ModelsLoader(QObject):
    loaded = Signal(list)
    failed = Signal(str)


class _SpeedRunner(QObject):
    row = Signal(str, object, str, str)  # modelo, Timing | None, texto, error
    finished = Signal()


def _pct_spin(lo: int, hi: int, value: float) -> QSpinBox:
    s = QSpinBox()
    s.setRange(lo, hi)
    s.setSuffix(" %")
    s.setValue(round(value * 100))
    return s


class SettingsWindow(QDialog):
    saved = Signal(object, str)  # (Settings, api_key o "" si no cambia)
    save_and_test = Signal()
    preview_requested = Signal(object)  # Settings (copia de trabajo)

    def __init__(self, settings: Settings, hub: InputHub, gemini: GeminiService,
                 capture_excluded: bool, api_status: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Overlay Gemini · Ajustes")
        self.setMinimumSize(760, 620)
        self.s = copy.deepcopy(settings)
        self.hub = hub
        self.gemini = gemini
        self._current_preset: Preset | None = None
        self._loader = _ModelsLoader()
        self._loader.loaded.connect(self._on_models_loaded)
        self._loader.failed.connect(self._on_models_failed)
        self._extra_models: list[str] = []
        self._api_status = api_status
        self._picker: RegionPicker | None = None
        self._speed = _SpeedRunner()
        self._speed.row.connect(self._on_speed_row)
        self._speed.finished.connect(self._on_speed_finished)
        self._speed_md: list[str] = []

        tabs = QTabWidget()
        tabs.addTab(self._build_general(capture_excluded), "General")
        tabs.addTab(self._build_prompts(), "Prompts")
        tabs.addTab(self._build_overlay(), "Franja")
        tabs.addTab(self._build_speed(), "Velocidad")

        buttons = QDialogButtonBox()
        self.btn_test = buttons.addButton("Guardar y probar", QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton("Guardar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        self.btn_test.clicked.connect(self._save_and_test)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

        self._learn_timer = QTimer(self)
        self._learn_timer.setSingleShot(True)
        self._learn_timer.timeout.connect(self._learn_timeout)
        hub.learned.connect(self._on_learned)
        hub.learn_cancelled.connect(self._on_learn_cancelled)

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_devices)
        self._status_timer.start(1000)
        self._refresh_devices()

    # ================================================================= General
    def _build_general(self, capture_excluded: bool) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)

        g = QGroupBox("Gemini")
        f = QFormLayout(g)
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("Pega aquí tu API key (aistudio.google.com/apikey)")
        self._initial_key = get_api_key()
        self.api_key.setText(self._initial_key)
        show = QPushButton("Ver")
        show.setCheckable(True)
        show.toggled.connect(lambda on: self.api_key.setEchoMode(
            QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password))
        row = QHBoxLayout()
        row.addWidget(self.api_key)
        row.addWidget(show)
        f.addRow("API key:", row)
        if api_key_from_env():
            self.api_key.setEnabled(False)
            f.addRow("", QLabel("Usando la variable de entorno GEMINI_API_KEY."))
        else:
            hint = QLabel('Consíguela gratis en <a href="https://aistudio.google.com/apikey">'
                          "aistudio.google.com/apikey</a>. Se guarda en el Administrador de "
                          "credenciales de Windows.")
            hint.setOpenExternalLinks(True)
            hint.setWordWrap(True)
            f.addRow("", hint)
        if self._api_status:
            status = QLabel(self._api_status)
            status.setWordWrap(True)
            status.setStyleSheet("color: #2e7d32" if self._api_status.startswith("✔") else "color: #c0392b")
            f.addRow("Estado:", status)

        self.global_model = self._model_combo(allow_empty=False)
        self._set_combo_text(self.global_model, self.s.model)
        load = QPushButton("Cargar modelos de la API")
        load.clicked.connect(self._load_models)
        row = QHBoxLayout()
        row.addWidget(self.global_model, 1)
        row.addWidget(load)
        f.addRow("Modelo:", row)
        self.global_model_desc = QLabel()
        self.global_model_desc.setStyleSheet("color: gray")
        self.global_model.currentTextChanged.connect(
            lambda t: self.global_model_desc.setText(self._model_desc(t)))
        self.global_model.currentTextChanged.connect(lambda _t: self._refresh_thinking())
        self.global_model_desc.setText(self._model_desc(self.s.model))
        f.addRow("", self.global_model_desc)

        self.active_preset = QComboBox()
        f.addRow("Prompt activo:", self.active_preset)
        v.addWidget(g)

        g = QGroupBox("Botón de captura / ocultar")
        f = QFormLayout(g)
        self.binding_label = QLabel()
        self.binding_label.setStyleSheet("font-weight: 600")
        self.btn_learn = QPushButton("Asignar…")
        self.btn_learn.clicked.connect(self._start_learn)
        clear = QPushButton("Quitar")
        clear.clicked.connect(self._clear_binding)
        row = QHBoxLayout()
        row.addWidget(self.binding_label, 1)
        row.addWidget(self.btn_learn)
        row.addWidget(clear)
        f.addRow("Botón:", row)
        self.long_press = QSpinBox()
        self.long_press.setRange(300, 3000)
        self.long_press.setSingleStep(100)
        self.long_press.setSuffix(" ms")
        self.long_press.setValue(self.s.long_press_ms)
        f.addRow("Pulsación larga:", self.long_press)
        f.addRow("", QLabel("Corta: captura ↔ oculta. Larga: vuelve a mostrar la última respuesta."))
        self.devices_label = QLabel()
        self.devices_label.setWordWrap(True)
        self.devices_label.setStyleSheet("color: gray")
        f.addRow("Mandos:", self.devices_label)
        self._update_binding_label()
        v.addWidget(g)

        g = QGroupBox("Captura")
        f = QFormLayout(g)
        self.screen = QComboBox()
        for i, scr in enumerate(QGuiApplication.screens()):
            self.screen.addItem(describe_screen(scr, i), scr.name())
        idx = self.screen.findData(self.s.screen_name)
        primary = QGuiApplication.primaryScreen()
        if idx < 0 and primary is not None:
            idx = self.screen.findData(primary.name())
        self.screen.setCurrentIndex(max(0, idx))
        f.addRow("Pantalla (captura y franja):", self.screen)
        self.max_width = QSpinBox()
        self.max_width.setRange(0, 7680)
        self.max_width.setSingleStep(320)
        self.max_width.setSpecialValueText("Original")
        self.max_width.setSuffix(" px")
        self.max_width.setValue(self.s.max_image_width)
        f.addRow("Ancho máx. de la imagen:", self.max_width)
        self.region_label = QLabel()
        pick = QPushButton("Elegir zona…")
        pick.clicked.connect(self._pick_region)
        full = QPushButton("Pantalla completa")
        full.clicked.connect(self._clear_region)
        row = QHBoxLayout()
        row.addWidget(self.region_label, 1)
        row.addWidget(pick)
        row.addWidget(full)
        f.addRow("Zona de captura:", row)
        tip = QLabel("Con el proyector de pantalla completa de OBS, deja «Pantalla completa». "
                     "Si ves el curso en la ventana de OBS, marca solo la vista previa.")
        tip.setWordWrap(True)
        tip.setStyleSheet("color: gray")
        f.addRow("", tip)
        self._update_region_label()
        self.exclude = QCheckBox("Ocultar la franja de OBS y de cualquier grabación")
        self.exclude.setChecked(self.s.exclude_from_capture)
        f.addRow("", self.exclude)
        if self.s.exclude_from_capture and not capture_excluded:
            warn = QLabel("⚠ Windows no ha permitido ocultar la franja (requiere Windows 10 2004 o "
                          "posterior). Podría salir en la grabación.")
            warn.setWordWrap(True)
            warn.setStyleSheet("color: #c0392b")
            f.addRow("", warn)
        v.addWidget(g)

        g = QGroupBox("Inicio")
        f = QFormLayout(g)
        self.autostart = QCheckBox("Arrancar con Windows (directamente en la bandeja, sin ventanas)")
        self._autostart_initial = autostart.is_enabled()
        self.autostart.setChecked(self._autostart_initial)
        if not autostart.supported():
            self.autostart.setEnabled(False)
            self.autostart.setToolTip("Solo disponible en Windows.")
        f.addRow(self.autostart)
        v.addWidget(g)
        v.addStretch(1)
        return w

    # ================================================================= Prompts
    def _build_prompts(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)

        left = QVBoxLayout()
        self.preset_list = QListWidget()
        self.preset_list.currentRowChanged.connect(self._on_preset_row)
        left.addWidget(self.preset_list, 1)
        row = QHBoxLayout()
        for text, slot in (("Nuevo", self._new_preset), ("Duplicar", self._dup_preset),
                           ("Borrar", self._del_preset)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            row.addWidget(b)
        left.addLayout(row)
        h.addLayout(left, 1)

        form_w = QWidget()
        f = QFormLayout(form_w)
        self.p_name = QLineEdit()
        f.addRow("Nombre:", self.p_name)
        self.p_model = self._model_combo(allow_empty=True)
        self.p_model.currentTextChanged.connect(lambda _t: self._refresh_thinking())
        f.addRow("Modelo:", self.p_model)
        self.p_thinking = QComboBox()
        f.addRow("Razonamiento:", self.p_thinking)
        self.p_resolution = QComboBox()
        for value, label in RESOLUTIONS:
            self.p_resolution.addItem(label, value)
        f.addRow("Resolución imagen:", self.p_resolution)
        self.p_search = QCheckBox("Buscar en Google para contrastar (5.000/mes gratis)")
        f.addRow("", self.p_search)
        self.p_max_tokens = QSpinBox()
        self.p_max_tokens.setRange(0, 65536)
        self.p_max_tokens.setSingleStep(256)
        self.p_max_tokens.setSpecialValueText("Sin límite")
        f.addRow("Máx. tokens salida:", self.p_max_tokens)
        self.p_system = QPlainTextEdit()
        self.p_system.setPlaceholderText("Instrucciones de sistema: rol, idioma, brevedad…")
        f.addRow("System instruction:", self.p_system)
        self.p_prompt = QPlainTextEdit()
        self.p_prompt.setPlaceholderText("Lo que se pide sobre cada captura")
        self.p_prompt.setMaximumHeight(110)
        f.addRow("Prompt:", self.p_prompt)
        h.addWidget(form_w, 3)

        self._reload_preset_list(select_id=self.s.active_preset().id)
        return w

    # ================================================================= Franja
    def _build_overlay(self) -> QWidget:
        w = QWidget()
        f = QFormLayout(w)
        o = self.s.overlay
        self.o_center = _pct_spin(10, 90, o.vertical_center)
        f.addRow("Posición vertical (centro):", self.o_center)
        self.o_width = _pct_spin(30, 100, o.max_width)
        f.addRow("Ancho máximo normal:", self.o_width)
        self.o_wide = _pct_spin(30, 100, o.wide_width)
        f.addRow("Ancho si no cabe:", self.o_wide)
        self.o_height = _pct_spin(10, 95, o.max_height)
        f.addRow("Alto máximo:", self.o_height)
        self.o_opacity = _pct_spin(20, 100, o.opacity)
        f.addRow("Opacidad del fondo:", self.o_opacity)
        self.o_font = QSpinBox()
        self.o_font.setRange(10, 48)
        self.o_font.setSuffix(" px")
        self.o_font.setValue(o.font_px)
        f.addRow("Tamaño de letra:", self.o_font)
        self.o_min_font = _pct_spin(40, 100, o.min_font_ratio)
        f.addRow("Letra mínima (si no cabe):", self.o_min_font)
        self.o_fade = QSpinBox()
        self.o_fade.setRange(0, 1000)
        self.o_fade.setSingleStep(20)
        self.o_fade.setSuffix(" ms")
        self.o_fade.setSpecialValueText("Sin animación")
        self.o_fade.setValue(o.fade_ms)
        f.addRow("Fundido al aparecer/ocultar:", self.o_fade)
        info = QLabel("La franja se ajusta sola al tamaño de cada respuesta: crece desde el "
                      "centro y, si no cabe, se ensancha y reduce la letra. Nunca hay que "
                      "hacer scroll.")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray")
        f.addRow(info)
        preview = QPushButton("Vista previa (5 s)")
        preview.clicked.connect(self._preview)
        f.addRow(preview)
        return w

    # ================================================================= helpers
    def _model_combo(self, allow_empty: bool) -> QComboBox:
        c = QComboBox()
        c.setEditable(True)
        c.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        if allow_empty:
            c.addItem("")
            c.lineEdit().setPlaceholderText("(usar el modelo global)")
        for mid, _desc in SUGGESTED_MODELS:
            c.addItem(mid)
        for mid in self._extra_models:
            if c.findText(mid) < 0:
                c.addItem(mid)
        return c

    @staticmethod
    def _set_combo_text(c: QComboBox, text: str) -> None:
        i = c.findText(text)
        if i >= 0:
            c.setCurrentIndex(i)
        else:
            c.setEditText(text)

    @staticmethod
    def _model_desc(model: str) -> str:
        for mid, desc in SUGGESTED_MODELS:
            if mid == model.strip():
                return desc
        return ""

    def _effective_model(self) -> str:
        return self.p_model.currentText().strip() or self.global_model.currentText().strip()

    def _refresh_thinking(self) -> None:
        if not hasattr(self, "p_thinking"):
            return
        current = self.p_thinking.currentData()
        if current is None and self._current_preset is not None:
            current = self._current_preset.thinking_level
        levels, default = thinking_levels(self._effective_model())
        self.p_thinking.blockSignals(True)
        self.p_thinking.clear()
        label_default = LEVEL_LABELS[""] + (f" ({LEVEL_LABELS[default].split(' (')[0].lower()})"
                                            if default else "")
        self.p_thinking.addItem(label_default, "")
        for lv in levels:
            self.p_thinking.addItem(LEVEL_LABELS.get(lv, lv), lv)
        i = self.p_thinking.findData(current or "")
        self.p_thinking.setCurrentIndex(max(0, i))
        self.p_thinking.blockSignals(False)

    # ----------------------------------------------------------------- presets
    def _reload_preset_list(self, select_id: str | None = None) -> None:
        self.preset_list.blockSignals(True)
        self.preset_list.clear()
        for p in self.s.presets:
            self.preset_list.addItem(p.name or "(sin nombre)")
        self.preset_list.blockSignals(False)
        active_id = self.active_preset.currentData() or self.s.active_preset_id
        self.active_preset.clear()
        for p in self.s.presets:
            self.active_preset.addItem(p.name or "(sin nombre)", p.id)
        i = self.active_preset.findData(active_id)
        self.active_preset.setCurrentIndex(max(0, i))
        row = next((i for i, p in enumerate(self.s.presets) if p.id == select_id), 0)
        self._current_preset = None
        self.preset_list.setCurrentRow(row)
        self._on_preset_row(row)

    def _store_form(self) -> None:
        p = self._current_preset
        if p is None:
            return
        p.name = self.p_name.text().strip() or "Sin nombre"
        p.model = self.p_model.currentText().strip()
        p.thinking_level = self.p_thinking.currentData() or ""
        p.resolution = self.p_resolution.currentData() or "high"
        p.google_search = self.p_search.isChecked()
        p.max_output_tokens = self.p_max_tokens.value()
        p.system_instruction = self.p_system.toPlainText().strip()
        p.prompt = self.p_prompt.toPlainText().strip()

    @Slot(int)
    def _on_preset_row(self, row: int) -> None:
        self._store_form()
        if row < 0 or row >= len(self.s.presets):
            return
        p = self.s.presets[row]
        self._current_preset = None  # evita que _refresh_thinking lea el preset anterior
        self.p_name.setText(p.name)
        self._set_combo_text(self.p_model, p.model)
        self._current_preset = p
        self.p_thinking.clear()
        self._refresh_thinking()
        i = self.p_thinking.findData(p.thinking_level or "")
        self.p_thinking.setCurrentIndex(max(0, i))
        i = self.p_resolution.findData(p.resolution or "high")
        self.p_resolution.setCurrentIndex(max(0, i))
        self.p_search.setChecked(p.google_search)
        self.p_max_tokens.setValue(p.max_output_tokens)
        self.p_system.setPlainText(p.system_instruction)
        self.p_prompt.setPlainText(p.prompt)

    def _new_preset(self) -> None:
        self._store_form()
        p = Preset(id=new_id(), name="Nuevo prompt",
                   system_instruction="Responde en español, directo al grano, en pocas líneas.",
                   prompt="")
        self.s.presets.append(p)
        self._current_preset = None
        self._reload_preset_list(select_id=p.id)

    def _dup_preset(self) -> None:
        self._store_form()
        if self._current_preset is None:
            return
        p = copy.deepcopy(self._current_preset)
        p.id = new_id()
        p.name = f"{p.name} (copia)"
        self.s.presets.append(p)
        self._current_preset = None
        self._reload_preset_list(select_id=p.id)

    def _del_preset(self) -> None:
        if self._current_preset is None or len(self.s.presets) <= 1:
            QMessageBox.information(self, "Prompts", "Tiene que quedar al menos un prompt.")
            return
        self.s.presets = [p for p in self.s.presets if p.id != self._current_preset.id]
        self._current_preset = None
        self._reload_preset_list(select_id=self.s.presets[0].id)

    # ----------------------------------------------------------------- botón
    def _update_binding_label(self) -> None:
        b = self.s.capture_binding
        self.binding_label.setText(b.describe() if b else "Sin asignar")

    def _start_learn(self) -> None:
        self.binding_label.setText("Pulsa ahora el botón del mando, ratón (X1/X2/central) o una tecla…  (Esc cancela)")
        self.btn_learn.setEnabled(False)
        self.hub.begin_learn()
        self._learn_timer.start(LEARN_TIMEOUT_MS)

    @Slot(object)
    def _on_learned(self, binding) -> None:
        self._learn_timer.stop()
        self.btn_learn.setEnabled(True)
        self.s.capture_binding = binding
        self._update_binding_label()

    @Slot()
    def _on_learn_cancelled(self) -> None:
        self._learn_timer.stop()
        self.btn_learn.setEnabled(True)
        self._update_binding_label()

    def _learn_timeout(self) -> None:
        self.hub.cancel_learn()
        self._on_learn_cancelled()

    def _clear_binding(self) -> None:
        self.s.capture_binding = None
        self._update_binding_label()

    def _refresh_devices(self) -> None:
        names = list(self.hub.gamepad.connected.values())
        text = ", ".join(names) if names else "ninguno detectado (conéctalo; si usas Steam, cierra Steam o desactiva Steam Input)"
        errors = self.hub.all_errors()
        if errors:
            text += "\n⚠ " + " · ".join(errors)
        self.devices_label.setText(text)

    # ----------------------------------------------------------------- modelos
    def _load_models(self) -> None:
        key = self.api_key.text().strip() or get_api_key()
        if not key:
            QMessageBox.warning(self, "Modelos", "Primero pega tu API key.")
            return

        def run():
            try:
                self._loader.loaded.emit(self.gemini.list_models(key))
            except Exception as e:  # noqa: BLE001
                self._loader.failed.emit(friendly_error(e))

        threading.Thread(target=run, daemon=True).start()

    @Slot(list)
    def _on_models_loaded(self, ids: list) -> None:
        self._extra_models = list(ids)
        for combo in (self.global_model, self.p_model):
            text = combo.currentText()
            for mid in ids:
                if combo.findText(mid) < 0:
                    combo.addItem(mid)
            self._set_combo_text(combo, text)
        QMessageBox.information(self, "Modelos", f"{len(ids)} modelos disponibles añadidos a la lista.")

    @Slot(str)
    def _on_models_failed(self, msg: str) -> None:
        QMessageBox.warning(self, "Modelos", msg)

    # ----------------------------------------------------------------- zona de captura
    def _update_region_label(self) -> None:
        r = self.s.capture_region
        if not r:
            self.region_label.setText("Pantalla completa")
        else:
            self.region_label.setText(
                f"Zona personalizada: {r[2] * 100:.0f} % × {r[3] * 100:.0f} % de la pantalla")

    def _clear_region(self) -> None:
        self.s.capture_region = None
        self._update_region_label()

    def _pick_region(self) -> None:
        screen = find_screen(self.screen.currentData() or "")
        self.hide()  # que la ventana de Ajustes no salga en la imagen congelada
        QTimer.singleShot(300, lambda: self._open_picker(screen))

    def _open_picker(self, screen) -> None:
        self._picker = RegionPicker(screen, self.s.capture_region)
        self._picker.picked.connect(self._on_region_picked)
        self._picker.show()
        self._picker.raise_()
        self._picker.activateWindow()

    @Slot(object)
    def _on_region_picked(self, region) -> None:
        if region != "cancel":
            self.s.capture_region = region
        self._picker = None
        self._update_region_label()
        self.show()
        self.raise_()
        self.activateWindow()

    # ----------------------------------------------------------------- comparar velocidad
    def _build_speed(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        info = QLabel(
            "Hace <b>una</b> captura (esta ventana se oculta un momento) y la envía con el "
            "<b>prompt activo</b> a cada modelo marcado, uno tras otro. Así ves cuánto tarda cada "
            "uno y cómo responde con tus prompts reales. Gasta una petición por modelo.")
        info.setWordWrap(True)
        v.addWidget(info)
        self.speed_models = QListWidget()
        self.speed_models.setMaximumHeight(150)
        default_on = {self.s.model, "gemini-3.5-flash-lite", "gemini-4-hydrogen"}
        seen: set[str] = set()
        for mid in [self.s.model] + [m for m, _ in SUGGESTED_MODELS]:
            if mid in seen:
                continue
            seen.add(mid)
            item = QListWidgetItem(mid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if mid in default_on else Qt.CheckState.Unchecked)
            self.speed_models.addItem(item)
        v.addWidget(self.speed_models)
        self.speed_btn = QPushButton("Capturar y comparar")
        self.speed_btn.clicked.connect(self._run_speed)
        v.addWidget(self.speed_btn)
        self.speed_table = QTableWidget(0, 4)
        self.speed_table.setHorizontalHeaderLabels(["Modelo", "Primer texto", "Total", "Líneas"])
        self.speed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.speed_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.speed_table.verticalHeader().setVisible(False)
        self.speed_table.setMaximumHeight(140)
        v.addWidget(self.speed_table)
        self.speed_text = QTextBrowser()
        self.speed_text.setPlaceholderText("Aquí aparecerán las respuestas de cada modelo.")
        v.addWidget(self.speed_text, 1)
        return w

    def _checked_speed_models(self) -> list[str]:
        out = []
        for i in range(self.speed_models.count()):
            item = self.speed_models.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                out.append(item.text())
        return out

    def _run_speed(self) -> None:
        key = self.api_key.text().strip() or get_api_key()
        if not key:
            QMessageBox.warning(self, "Comparar velocidad", "Primero pega tu API key.")
            return
        models = self._checked_speed_models()
        if not models:
            QMessageBox.information(self, "Comparar velocidad", "Marca al menos un modelo.")
            return
        settings = copy.deepcopy(self._collect())
        self.hide()
        QTimer.singleShot(350, lambda: self._speed_capture(key, models, settings))

    def _speed_capture(self, key: str, models: list[str], settings: Settings) -> None:
        try:
            image = grab_image(settings.screen_name)
        except Exception as e:  # noqa: BLE001
            self.show()
            QMessageBox.warning(self, "Comparar velocidad", f"No se pudo capturar la pantalla: {e}")
            return
        self.show()
        self.raise_()
        self.activateWindow()
        self.speed_btn.setEnabled(False)
        self.speed_btn.setText("Comparando…")
        self.speed_table.setRowCount(0)
        self.speed_text.clear()
        self._speed_md = []
        preset = settings.active_preset()

        def run():
            try:
                jpeg = prepare_image(image, settings.capture_region, settings.max_image_width)
                for mid in models:
                    p = copy.deepcopy(preset)
                    p.model = mid
                    try:
                        text, timing, _ = self.gemini.measure(key, build_request(p, settings, jpeg))
                        self._speed.row.emit(mid, timing, text, "")
                    except Exception as e:  # noqa: BLE001
                        self._speed.row.emit(mid, None, "", friendly_error(e))
            except Exception as e:  # noqa: BLE001
                self._speed.row.emit("-", None, "", str(e))
            finally:
                self._speed.finished.emit()

        threading.Thread(target=run, daemon=True).start()

    @Slot(str, object, str, str)
    def _on_speed_row(self, model: str, timing, text: str, error: str) -> None:
        r = self.speed_table.rowCount()
        self.speed_table.insertRow(r)
        fmt = lambda t: "-" if t is None else f"{t:.1f} s".replace(".", ",")  # noqa: E731
        lines = len([ln for ln in text.splitlines() if ln.strip()])
        cells = [model, fmt(timing.first_text) if timing else "error",
                 fmt(timing.total) if timing else "-", str(lines) if timing else "-"]
        for c, value in enumerate(cells):
            self.speed_table.setItem(r, c, QTableWidgetItem(value))
        title = f"### {model} · {fmt(timing.total)}" if timing else f"### {model} · error"
        self._speed_md.append(f"{title}\n\n{text if timing else error}\n")
        self.speed_text.setMarkdown("\n---\n".join(self._speed_md))

    @Slot()
    def _on_speed_finished(self) -> None:
        self.speed_btn.setEnabled(True)
        self.speed_btn.setText("Capturar y comparar")

    # ----------------------------------------------------------------- guardar
    def _collect(self) -> Settings:
        self._store_form()
        s = self.s
        s.model = self.global_model.currentText().strip() or s.model
        s.active_preset_id = self.active_preset.currentData() or s.active_preset_id
        s.long_press_ms = self.long_press.value()
        s.screen_name = self.screen.currentData() or ""
        s.max_image_width = self.max_width.value()
        s.exclude_from_capture = self.exclude.isChecked()
        o = s.overlay
        o.vertical_center = self.o_center.value() / 100
        o.max_width = self.o_width.value() / 100
        o.wide_width = max(o.max_width, self.o_wide.value() / 100)
        o.max_height = self.o_height.value() / 100
        o.opacity = self.o_opacity.value() / 100
        o.font_px = self.o_font.value()
        o.min_font_ratio = self.o_min_font.value() / 100
        o.fade_ms = self.o_fade.value()
        return s

    def _preview(self) -> None:
        self.preview_requested.emit(copy.deepcopy(self._collect()))

    def _key_to_save(self) -> str | None:
        if api_key_from_env():
            return None
        key = self.api_key.text().strip()
        return key if key != self._initial_key else None

    def _do_save(self) -> bool:
        s = self._collect()
        key = self._key_to_save()
        if key is not None:
            try:
                set_api_key(key)
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, "API key", f"No se pudo guardar la API key: {e}")
                return False
        wanted = self.autostart.isChecked()
        if autostart.supported() and wanted != self._autostart_initial:
            try:
                autostart.set_enabled(wanted)
                self._autostart_initial = wanted
            except Exception as e:  # noqa: BLE001
                QMessageBox.critical(self, "Arrancar con Windows",
                                     f"No se pudo cambiar el arranque automático: {e}")
                return False
        self.saved.emit(copy.deepcopy(s), key or "")
        return True

    def _save(self) -> None:
        if self._do_save():
            self.accept()

    def _save_and_test(self) -> None:
        if self._do_save():
            self.accept()
            self.save_and_test.emit()

    def done(self, result: int) -> None:  # noqa: D401 (Qt)
        if self.hub.learning:
            self.hub.cancel_learn()
        self._status_timer.stop()
        try:
            self.hub.learned.disconnect(self._on_learned)
            self.hub.learn_cancelled.disconnect(self._on_learn_cancelled)
        except (RuntimeError, TypeError):
            pass
        super().done(result)

