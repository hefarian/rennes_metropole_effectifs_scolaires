# Sauvegarde de la base PostgreSQL dans le dossier backups/
Set-Location $PSScriptRoot\..

$BackupDir = "backups\postgres"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Project   = (Get-Content .env | Select-String "COMPOSE_PROJECT_NAME=(.+)" | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }) -replace '\s',''
$DbName    = (Get-Content .env | Select-String "POSTGRES_DB=(.+)"          | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }) -replace '\s',''
$DbUser    = (Get-Content .env | Select-String "POSTGRES_USER=(.+)"        | ForEach-Object { $_.Matches[0].Groups[1].Value.Trim() }) -replace '\s',''
$OutFile   = "$BackupDir\${Project}_${DbName}_${Timestamp}.sql"

Write-Host "[P13] Sauvegarde de $DbName → $OutFile" -ForegroundColor Cyan

docker compose exec -T postgres pg_dump -U $DbUser $DbName | Set-Content $OutFile -Encoding UTF8

if ($LASTEXITCODE -eq 0 -and (Test-Path $OutFile) -and (Get-Item $OutFile).Length -gt 1024) {
    $SizeKB = [math]::Round((Get-Item $OutFile).Length / 1024, 1)
    Write-Host "[P13] Backup OK : $OutFile ($SizeKB KB)" -ForegroundColor Green
} else {
    Write-Host "[P13] ERREUR : backup vide ou echec pg_dump." -ForegroundColor Red
    exit 1
}
