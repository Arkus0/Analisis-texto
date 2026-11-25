"""Genera dist/OverlayGemini/OverlayGemini.exe con PyInstaller.

    python build.py
"""

import sys
from pathlib import Path

import PyInstaller.__main__

HERE = Path(__file__).resolve().parent

args = [
    str(HERE / "main.py"),
    "--name", "OverlayGemini",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--distpath", str(HERE / "dist"),
    "--workpath", str(HERE / "build"),
    "--specpath", str(HERE / "build"),
    "--paths", str(HERE),
    "--additional-hooks-dir", str(HERE / "pyinstaller_hooks"),
    "--collect-all", "sdl2dll",  # SDL2.dll para los mandos
    "--hidden-import", "pynput.keyboard._win32",
    "--hidden-import", "pynput.mouse._win32",
    "--hidden-import", "keyring.backends.Windows",
    "--exclude-module", "pytest",
    "--exclude-module", "tkinter",
    "--exclude-module", "PIL",
]

if __name__ == "__main__":
    PyInstaller.__main__.run(args + sys.argv[1:])
