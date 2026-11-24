@echo off
rem Crea un entorno virtual, instala dependencias y genera dist\OverlayGemini\OverlayGemini.exe
setlocal
cd /d "%~dp0"
if not exist .venv (
    py -3 -m venv .venv || python -m venv .venv || goto :error
)
call .venv\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
pip install -r requirements-dev.txt || goto :error
python -m pytest -q || goto :error
python build.py || goto :error
dist\OverlayGemini\OverlayGemini.exe --selftest selftest.log
type selftest.log
echo.
echo Listo: dist\OverlayGemini\OverlayGemini.exe
goto :eof

:error
echo.
echo *** Ha fallado la compilacion ***
exit /b 1
