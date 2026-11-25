# El SDK de Gemini carga muchos módulos de forma perezosa (lazy imports), así que
# PyInstaller no los ve: se incluyen todos explícitamente, menos los tests.
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("google.genai", filter=lambda name: ".tests" not in name)
datas = collect_data_files("google.genai", excludes=["**/tests/**"])
