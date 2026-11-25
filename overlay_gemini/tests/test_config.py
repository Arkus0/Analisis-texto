import json

from app.config import (
    Binding,
    Preset,
    default_settings,
    load_settings,
    save_settings,
    settings_from_dict,
    settings_to_dict,
)
from app.models import DEFAULT_MODEL


def test_defaults_have_three_presets_and_current_model():
    s = default_settings()
    assert [p.name for p in s.presets] == ["Dudas", "Definición exacta", "Traducción"]
    assert s.model == DEFAULT_MODEL == "gemini-4-hydrogen"
    assert s.active_preset().id == "dudas"
    assert s.exclude_from_capture is True
    assert s.capture_binding is None
    # Todos los prompts por defecto piden brevedad para que quepan en la franja.
    assert all("grano" in p.system_instruction or "8 líneas" in p.system_instruction for p in s.presets)
    assert next(p for p in s.presets if p.id == "definicion").google_search is True


def test_round_trip(tmp_path):
    s = default_settings()
    s.capture_binding = Binding("gamepad", "a", "Mando: A")
    s.presets.append(Preset(id="x", name="Resumen", system_instruction="si", prompt="p",
                            model="gemini-3.5-flash-lite", thinking_level="minimal",
                            resolution="ultra_high", max_output_tokens=500))
    s.active_preset_id = "x"
    s.overlay.font_px = 25
    path = tmp_path / "c.json"
    save_settings(s, path)
    loaded = load_settings(path)
    assert settings_to_dict(loaded) == settings_to_dict(s)
    assert loaded.active_preset().name == "Resumen"
    assert loaded.model_for(loaded.active_preset()) == "gemini-3.5-flash-lite"


def test_unknown_and_missing_keys_are_tolerated():
    s = settings_from_dict({
        "model": "gemini-3.8-flash",
        "futuro": 1,
        "presets": [{"id": "a", "name": "A", "prompt": "hola", "campo_nuevo": True}],
        "active_preset_id": "no-existe",
        "capture_binding": {"kind": "mouse", "code": "x1"},
        "overlay": {"font_px": 30, "otro": 2},
    })
    assert s.model == "gemini-3.8-flash"
    assert s.active_preset().id == "a"  # se repara el id activo
    assert s.presets[0].system_instruction == ""
    assert s.capture_binding == Binding("mouse", "x1", "")
    assert s.overlay.font_px == 30
    assert s.overlay.max_height == default_settings().overlay.max_height


def test_corrupt_file_falls_back_to_defaults(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{no es json", encoding="utf-8")
    s = load_settings(path)
    assert len(s.presets) == 3
    assert (tmp_path / "config.corrupt.json").exists()


def test_missing_file_gives_defaults(tmp_path):
    assert load_settings(tmp_path / "nada.json").model == DEFAULT_MODEL


def test_model_for_uses_global_when_preset_empty():
    s = default_settings()
    s.model = "gemini-4-carbon"
    p = s.active_preset()
    p.model = "  "
    assert s.model_for(p) == "gemini-4-carbon"


def test_saved_file_is_utf8_readable(tmp_path):
    path = tmp_path / "c.json"
    save_settings(default_settings(), path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["presets"][1]["name"] == "Definición exacta"


def test_new_fields_and_region_validation():
    from app.config import normalize_region

    s = default_settings()
    assert s.capture_region is None and s.wait_timeout_s == 40 and s.overlay.fade_ms > 0
    assert normalize_region([0.1, 0.2, 0.5, 0.5]) == [0.1, 0.2, 0.5, 0.5]
    assert normalize_region([0.8, 0.8, 0.5, 0.5]) == [0.8, 0.8, 0.2, 0.2]  # recortada al borde
    assert normalize_region([0, 0, 1, 1]) is None
    assert normalize_region("basura") is None
    assert normalize_region([0.1, 0.1, 0.001, 0.5]) is None
    loaded = settings_from_dict({**settings_to_dict(s), "capture_region": [0.1, 0.1, 0.6, 0.6]})
    assert loaded.capture_region == [0.1, 0.1, 0.6, 0.6]
    assert settings_from_dict({"capture_region": [9, 9]}).capture_region is None
