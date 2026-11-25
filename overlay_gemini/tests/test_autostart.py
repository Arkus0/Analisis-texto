import sys

import pytest

from app import autostart


class DictRegistry:
    def __init__(self):
        self.values = {}

    def get(self, name):
        return self.values.get(name)

    def set(self, name, value):
        self.values[name] = value

    def delete(self, name):
        self.values.pop(name, None)


def test_command_for_packaged_exe():
    cmd = autostart.launch_command(r"C:\Program Files\OverlayGemini\OverlayGemini.exe", frozen=True)
    assert cmd == r'"C:\Program Files\OverlayGemini\OverlayGemini.exe" --autostart'


def test_command_from_source_prefers_pythonw(tmp_path):
    (tmp_path / "python.exe").write_bytes(b"")
    (tmp_path / "pythonw.exe").write_bytes(b"")
    cmd = autostart.launch_command(str(tmp_path / "python.exe"), frozen=False, script=r"C:\app\main.py")
    assert cmd == f'"{tmp_path / "pythonw.exe"}" "C:\\app\\main.py" --autostart'


def test_command_from_source_without_pythonw_keeps_interpreter(tmp_path):
    (tmp_path / "python.exe").write_bytes(b"")
    cmd = autostart.launch_command(str(tmp_path / "python.exe"), frozen=False, script="main.py")
    assert cmd.startswith(f'"{tmp_path / "python.exe"}"') and cmd.endswith("--autostart")


def test_enable_disable_with_fake_registry():
    reg = DictRegistry()
    assert not autostart.is_enabled(reg)
    assert autostart.set_enabled(True, reg, command='"X.exe" --autostart')
    assert autostart.is_enabled(reg) and reg.values[autostart.VALUE_NAME] == '"X.exe" --autostart'
    assert autostart.set_enabled(False, reg)
    assert not autostart.is_enabled(reg) and reg.values == {}


def test_refresh_path_fixes_moved_exe_only_when_enabled():
    reg = DictRegistry()
    assert not autostart.refresh_path(reg, command='"nuevo.exe" --autostart')  # desactivado: nada
    assert reg.values == {}
    reg.set(autostart.VALUE_NAME, '"viejo.exe" --autostart')
    assert autostart.refresh_path(reg, command='"nuevo.exe" --autostart')
    assert reg.values[autostart.VALUE_NAME] == '"nuevo.exe" --autostart'
    assert not autostart.refresh_path(reg, command='"nuevo.exe" --autostart')  # ya estaba bien


def test_registry_errors_do_not_crash_reads():
    class Broken(DictRegistry):
        def get(self, name):
            raise OSError("acceso denegado")

    assert not autostart.is_enabled(Broken())
    assert not autostart.refresh_path(Broken(), command="x")


@pytest.mark.skipif(sys.platform == "win32", reason="fuera de Windows")
def test_noop_outside_windows():
    assert not autostart.supported()
    assert not autostart.is_enabled()
    assert not autostart.set_enabled(True)
    assert not autostart.refresh_path()


@pytest.mark.skipif(sys.platform != "win32", reason="solo en Windows (CI)")
def test_real_run_key_roundtrip():
    name = "OverlayGeminiTest"
    reg = autostart.WinRunKey()
    try:
        autostart.set_enabled(True, reg, name=name, command='"C:\\x\\OverlayGemini.exe" --autostart')
        assert autostart.is_enabled(reg, name=name)
        assert reg.get(name) == '"C:\\x\\OverlayGemini.exe" --autostart'
    finally:
        autostart.set_enabled(False, reg, name=name)
    assert not autostart.is_enabled(reg, name=name)
