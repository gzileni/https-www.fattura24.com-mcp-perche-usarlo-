$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Docker Desktop non installato. Installalo manualmente: https://docs.docker.com/desktop/setup/install/windows-install/'
    exit 1
}
docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) {
    $exe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
    if (Test-Path $exe) {
        Write-Host 'Provo ad aprire Docker Desktop ...'
        Start-Process $exe
        for ($i=0; $i -lt 40; $i++) {
            Start-Sleep -Seconds 2
            docker info --format '{{.ServerVersion}}' *> $null
            if ($LASTEXITCODE -eq 0) { break }
        }
    }
}
docker info --format '{{.ServerVersion}}' *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine non disponibile. Avvia Docker Desktop e riprova.' }
if (-not (Test-Path .env)) {
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $token = [System.BitConverter]::ToString($bytes).Replace('-', '')
    "BRIDGE_TOKEN=$token" | Set-Content -Path .env -Encoding ascii
    Write-Host 'Creato .env privato. Non pubblicarlo su GitHub.'
}
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Avvio Docker fallito.' }
Write-Host 'Verifica il bridge: http://127.0.0.1:8765/health'
