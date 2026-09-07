@echo off
REM ============================================================
REM Script de lancement du pipeline ETL
REM À utiliser avec le Planificateur de tâches Windows
REM ============================================================

REM Définir l'encodage UTF-8 pour les caractères français
chcp 65001 > nul

REM Obtenir le chemin du script et se positionner dans le dossier parent
cd /d "%~dp0.."

REM Vérifier que nous sommes dans le bon dossier
if not exist "main.py" (
    echo ERREUR: Fichier main.py introuvable!
    echo Chemin actuel: %CD%
    pause
    exit /b 1
)

REM Créer le dossier logs s'il n'existe pas
if not exist "logs" mkdir logs

REM Activer l'environnement virtuel
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Lancer le pipeline Python
python main.py

REM Capturer le code de sortie
set EXIT_CODE=%ERRORLEVEL%

REM Logger la date et l'heure d'exécution
echo [%date% %time%] Pipeline termine avec le code: %EXIT_CODE% >> logs\scheduler.log

REM Logger l'échec
if %EXIT_CODE% NEQ 0 (
    echo [%date% %time%] ERREUR: Pipeline echoue! >> logs\scheduler.log
)

exit /b %EXIT_CODE%