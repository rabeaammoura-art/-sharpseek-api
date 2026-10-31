@echo off
REM Usage: drag a plaque .json file (e.g. plaque\example_ar.json) onto this file, or: make_plaque.bat plaque\example_ar.json
cd /d "%~dp0"
..\.venv-cad\Scripts\python newborn_plaque.py %* --out out\plaque
echo.
echo Files are in the cad\out\plaque folder (open the .3mf in Bambu Studio).
pause
