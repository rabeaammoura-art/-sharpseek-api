@echo off
REM One-time setup of the plaque generator on Windows (needs Python 3.10+ from python.org, "Add to PATH" ticked).
cd /d "%~dp0.."
if not exist .venv-cad (
  py -3 -m venv .venv-cad
  if errorlevel 1 goto :fail
)
.venv-cad\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :fail
.venv-cad\Scripts\python.exe -m pip install -r cad\requirements-plaque.txt
if errorlevel 1 goto :fail
REM optional extras: better mesh quality and closed solids (if this fails, everything still works)
.venv-cad\Scripts\python.exe -m pip install triangle manifold3d
echo.
echo Setup finished OK. Now drag a plaque .json file onto make_plaque.bat
pause
exit /b 0
:fail
echo.
echo SETUP FAILED - send a screenshot of this window.
pause
exit /b 1
