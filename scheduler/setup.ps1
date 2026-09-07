# ============================================================
# Script PowerShell pour planifier le pipeline ETL
# Exécution automatique tous les jours à minuit (heure française)
# ============================================================

# Obtenir le chemin absolu du projet (dossier parent de scheduler)
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDirectory

# Définir les paramètres
$TaskName = "ETL_Pipeline_Books"
$ScriptPath = Join-Path $ScriptDirectory "run.bat"
$PythonScript = Join-Path $ProjectRoot "main.py"
$WorkingDirectory = $ProjectRoot
$LogPath = Join-Path $ProjectRoot "logs\scheduler.log"

# Heure d'exécution (minuit heure française)
$ExecutionTime = "00:00"

Write-Host "============================================================"
Write-Host "Configuration du Planificateur de taches Windows"
Write-Host "============================================================" 
Write-Host ""
Write-Host "Chemin du projet: $ProjectRoot" -ForegroundColor Cyan
Write-Host "Script BAT: $ScriptPath" -ForegroundColor Cyan
Write-Host ""

# Vérifier que les fichiers existent
if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERREUR: Script run.bat introuvable a: $ScriptPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PythonScript)) {
    Write-Host "ERREUR: Script main.py introuvable a: $PythonScript" -ForegroundColor Red
    exit 1
}

# Créer le dossier logs s'il n'existe pas
$LogFolder = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogFolder)) {
    New-Item -ItemType Directory -Path $LogFolder | Out-Null
    Write-Host "Dossier logs cree" -ForegroundColor Green
}

# Vérifier si la tâche existe déjà
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

if ($ExistingTask) {
    Write-Host "La tache '$TaskName' existe deja." -ForegroundColor Yellow
    $Response = Read-Host "Voulez-vous la supprimer et la recreer? (O/N)"
    
    if ($Response -eq "O" -or $Response -eq "o") {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Tache existante supprimee" -ForegroundColor Green
    } 
    else {
        Write-Host "Operation annulee" -ForegroundColor Red
        exit
    }
}

# exécuter le script BAT
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $WorkingDirectory

# tous les jours à minuit
$Trigger = New-ScheduledTaskTrigger -Daily -At $ExecutionTime

# Paramètres de la tâche
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

# Définir l'utilisateur
$Principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Highest

try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $Action `
        -Trigger $Trigger `
        -Settings $Settings `
        -Principal $Principal `
        -Description "Pipeline ETL automatique pour l'analyse des livres - Execution quotidienne a minuit"

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "TACHE CREEE AVEC SUCCES" -ForegroundColor Green
    Write-Host "============================================================" 
    Write-Host ""
    Write-Host "Nom de la tache: $TaskName" -ForegroundColor Cyan
    Write-Host "Heure d'execution: $ExecutionTime (tous les jours)" -ForegroundColor Cyan
    Write-Host "Chemin des logs: $LogPath" -ForegroundColor Cyan
    Write-Host ""
    
    $TestNow = Read-Host "Voulez-vous tester l execution maintenant ? (O/N)"
    
    if ($TestNow -eq "O" -or $TestNow -eq "o") {
        Write-Host ""
        Write-Host "Lancement du test..." -ForegroundColor Cyan
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2
        Write-Host "Tache lancee avec succes" -ForegroundColor Green
        Write-Host "Verifiez les logs dans: $LogPath" -ForegroundColor Cyan
    }
} catch {
    Write-Host ""
    Write-Host "ERREUR lors de la creation de la tache" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}