# Restaure la base PostgreSQL depuis un fichier SQL
# Usage : .\restore-db.ps1 -BackupFile backups\postgres\p13_dev_p13_scolarite_20260706_120000.sql
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile
)

Set-Location $PSScriptRoot\..

if (-not (Test-Path $BackupFile)) {
    Write-Host "Fichier introuvable : $BackupFile" -ForegroundColor Red
    exit 1
}

$DbName = (Get-Content .env | Select-String "POSTGRES_DB=(.+)"   | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }) -replace '\s',''
$DbUser = (Get-Content .env | Select-String "POSTGRES_USER=(.+)" | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }) -replace '\s',''

Write-Host "[P13] Restauration de $DbName depuis $BackupFile" -ForegroundColor Yellow
$confirm = Read-Host "Confirmer la restauration ? (oui/non)"
if ($confirm -ne "oui") { Write-Host "Annule."; exit 0 }

Get-Content $BackupFile | docker compose exec -T postgres psql -U $DbUser $DbName

if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] Restauration terminee." -ForegroundColor Green
} else {
    Write-Host "[P13] ERREUR lors de la restauration." -ForegroundColor Red
    exit 1
}
