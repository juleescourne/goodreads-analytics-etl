@echo off
setlocal
cd /d "%~dp0"
echo Configuration du rapport avec les donnees de ce dossier...
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "scripts\configurer_powerbi.py" --ouvrir
    goto :fin
)
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "scripts\configurer_powerbi.py" --ouvrir
    goto :fin
)
python "scripts\configurer_powerbi.py" --ouvrir
:fin
if errorlevel 1 (
    echo.
    echo Configuration interrompue. Consultez le message ci-dessus.
    pause
)
endlocal
