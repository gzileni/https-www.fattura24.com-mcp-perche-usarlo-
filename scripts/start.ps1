$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker Desktop non installato. Installa Docker dal sito ufficiale: https://docs.docker.com/desktop/setup/install/windows-install/'
}
docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) {
    $exe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
    if (Test-Path $exe) {
        Write-Host 'Docker e installato ma spento: provo ad avviare Docker Desktop.'
        Start-Process $exe
        for ($i=0; $i -lt 40; $i++) {
            Start-Sleep -Seconds 2
            docker info --format '{{.ServerVersion}}' *> $null
            if ($LASTEXITCODE -eq 0) { break }
        }
    }
}
docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine non disponibile. Verifica WSL2 e Docker Desktop.' }
if (-not (Test-Path .env)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $token = [System.BitConverter]::ToString($bytes).Replace('-', '')
    @("BRIDGE_TOKEN=$token", "FATTURA24_ENABLE_WRITES=false") | Set-Content -Path .env -Encoding ascii
    Write-Host 'Creato .env con scritture Fattura24 disattivate.'
}
Write-Host 'Scarico la versione pubblicata su GitHub Container Registry...'
docker compose pull
if ($LASTEXITCODE -ne 0) { throw 'Download fallito. Verifica che il pacchetto GHCR sia pubblico.' }
docker compose up -d --no-build
if ($LASTEXITCODE -ne 0) { throw 'Avvio container fallito.' }
Write-Host 'Verifica http://127.0.0.1:8765/health'
