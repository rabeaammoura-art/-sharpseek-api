@echo off
REM One-time setup of the plaque generator on Windows (needs Python 3.10+ from python.org, "Add to PATH" ticked).
cd /d "%~dp0.."
if not exist .venv-cad py -3 -m venv .venv-cad
.venv-cad\Scripts\python -m pip install --upgrade pip
.venv-cad\Scripts\pip install -r cad\requirements-plaque.txt
echo.
echo Setup done. Now drag a plaque .json file onto make_plaque.bat
pause
