#!/usr/bin/env pwsh
<#
.SYNOPSIS
Installe et configure le runner GitHub Actions Windows pour P13-PROD.

.DESCRIPTION
Script de setup du runner CI/CD du repo P13 effectifs scolaires:
- La branche main deploie vers G:\GITHUB\P13-PROD
- Le job cible les labels: self-hosted, windows, p13-deploy

.PARAMETER GithubPat
PAT GitHub avec permissions repo + workflow.

.PARAMETER Owner
Proprietaire du repo GitHub.

.PARAMETER Repo
Nom du repo GitHub.

.PARAMETER RunnerName
Nom du runner dans GitHub.

.PARAMETER RunnerDir
Dossier local d'installation du runner.

.PARAMETER Labels
Labels du runner (doivent inclure self-hosted,windows,p13-deploy).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$GithubPat,

    [string]$Owner = "hefarian",
    [string]$Repo = "rennes_metropole_effectifs_scolaires",
    [string]$RunnerName = "p13-prod-runner",
    [string]$RunnerDir = "G:\actions-runner\p13-prod",
    [string]$Labels = "self-hosted,windows,p13-deploy,p13-prod",
    [string]$WindowsLogonAccount = "NT AUTHORITY\SYSTEM",
    [switch]$UserMode
)

$ErrorActionPreference = "Stop"

function Write-Success { param([string]$Message) Write-Host $Message -ForegroundColor Green }
function Write-Err    { param([string]$Message) Write-Host $Message -ForegroundColor Red }
function Write-Info   { param([string]$Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warn   { param([string]$Message) Write-Host $Message -ForegroundColor Yellow }

function Test-IsAdmin {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-RegistrationToken {
    param([string]$Owner, [string]$Repo, [string]$Pat)
    $headers = @{
        Authorization            = "Bearer $Pat"
        Accept                   = "application/vnd.github+json"
        "X-GitHub-Api-Version"   = "2022-11-28"
    }
    $uri = "https://api.github.com/repos/$Owner/$Repo/actions/runners/registration-token"
    $response = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers
    if (-not $response.token) { throw "Impossible d'obtenir le token d'enregistrement." }
    return $response.token
}

Clear-Host
Write-Info "========================================="
Write-Info "Setup Runner GitHub - P13-PROD"
Write-Info "========================================="
Write-Info "Repo: https://github.com/$Owner/$Repo"
Write-Info "RunnerName: $RunnerName"
Write-Info "RunnerDir: $RunnerDir"
Write-Info "Labels: $Labels"
if (-not $UserMode) { Write-Info "Service account: $WindowsLogonAccount" }
Write-Info "Target deploy dir: G:\GITHUB\P13-PROD"
Write-Info "Ports PROD: API 28000 | Streamlit 28501 | MLflow 25000 | Jupyter 28888"

$isAdmin = Test-IsAdmin
if (-not $isAdmin -and -not $UserMode) {
    throw "Ce script doit etre execute en PowerShell Admin. Ajoute -UserMode pour un lancement manuel."
}

if (Test-Path $RunnerDir) {
    Write-Warn "Le dossier runner existe deja: $RunnerDir"
    if (Test-Path (Join-Path $RunnerDir "config.cmd")) {
        Write-Info "Runner detecte, reutilisation (mode --replace)."
    }
} else {
    New-Item -Path $RunnerDir -ItemType Directory -Force | Out-Null
}

$runnerZip     = Join-Path $RunnerDir "actions-runner.zip"
$runnerVersion = "2.327.1"
$downloadUrl   = "https://github.com/actions/runner/releases/download/v$runnerVersion/actions-runner-win-x64-$runnerVersion.zip"

if (-not (Test-Path (Join-Path $RunnerDir "config.cmd"))) {
    Write-Info "[1/5] Telechargement du runner..."
    Invoke-WebRequest -Uri $downloadUrl -OutFile $runnerZip
    Write-Success "Telechargement termine"
    Write-Info "[2/5] Extraction..."
    Expand-Archive -Path $runnerZip -DestinationPath $RunnerDir -Force
    Remove-Item -Path $runnerZip -Force
    Write-Success "Extraction terminee"
} else {
    Write-Info "[1/5] Runner deja present, telechargement ignore"
    Write-Info "[2/5] Extraction ignoree"
}

Write-Info "[3/5] Recuperation du token d'enregistrement GitHub..."
$registrationToken = Get-RegistrationToken -Owner $Owner -Repo $Repo -Pat $GithubPat
Write-Success "Token runner recupere"

Push-Location $RunnerDir
try {
    if (Test-Path (Join-Path $RunnerDir ".runner")) {
        Write-Warn "Runner deja configure. Nettoyage avant reconfiguration..."
        & .\config.cmd remove --local --unattended
        if ($LASTEXITCODE -ne 0) { throw "Echec config.cmd remove --local" }
        Write-Success "Configuration precedente supprimee"
    }

    Write-Info "[4/5] Configuration du runner..."
    $configArgs = @(
        "--url", "https://github.com/$Owner/$Repo",
        "--token", $registrationToken,
        "--name", $RunnerName,
        "--runnergroup", "Default",
        "--labels", $Labels,
        "--work", "_work",
        "--replace",
        "--unattended"
    )

    if (-not $UserMode) {
        $configArgs += "--runasservice"
        $configArgs += "--windowslogonaccount"
        $configArgs += $WindowsLogonAccount
    }

    & .\config.cmd @configArgs

    if ($LASTEXITCODE -ne 0 -and -not $UserMode) {
        Write-Warn "Echec mode service. Bascule vers mode manuel..."
        & .\config.cmd remove --local --unattended
        $manualArgs = @(
            "--url", "https://github.com/$Owner/$Repo",
            "--token", $registrationToken,
            "--name", $RunnerName,
            "--runnergroup", "Default",
            "--labels", $Labels,
            "--work", "_work",
            "--replace",
            "--unattended"
        )
        & .\config.cmd @manualArgs
        if ($LASTEXITCODE -ne 0) { throw "Echec config.cmd (mode manuel)" }
        Write-Success "Runner configure en mode manuel (fallback)"
        Write-Info "Lancer le runner manuellement:"
        Write-Info "  Set-Location $RunnerDir"
        Write-Info "  .\run.cmd"
        return
    }

    if ($LASTEXITCODE -ne 0) { throw "Echec config.cmd" }
    Write-Success "Runner configure"

    if ($UserMode) {
        Write-Info "[5/5] Mode utilisateur actif - service non installe"
        Write-Info "Lancer le runner manuellement:"
        Write-Info "  Set-Location $RunnerDir"
        Write-Info "  .\run.cmd"
    } else {
        Write-Info "[5/5] Service runner configure via --runasservice"
        Write-Success "Service runner pret"
    }
}
finally {
    Pop-Location
}

Write-Info ""
Write-Success "========================================="
Write-Success "Runner P13-PROD pret"
Write-Success "========================================="
Write-Info "Verification GitHub: https://github.com/$Owner/$Repo/settings/actions/runners"
Write-Info "Le runner doit apparaitre avec les labels: $Labels"
Write-Info "Ce runner executera le job deploy-main (branche main -> G:\GITHUB\P13-PROD)."

exit 0
