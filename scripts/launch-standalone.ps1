param([switch]$ReplaceExisting)
# Windows launcher: Docker only; no Git, Python or Compose.
$ErrorActionPreference = 'Stop'
$Image = 'ghcr.io/gzileni/fattura24-mcp-bridge:latest'
$Name = 'fattura24-mcp'
$Dir = Join-Path $env:LOCALAPPDATA 'Fattura24MCP'
$EnvFile = Join-Path $Dir 'bridge.env'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'Docker Desktop non installato.' }
function IsReady {
  try { docker info --format '{{.ServerVersion}}' 2>$null | Out-Null; return ($LASTEXITCODE -eq 0) }
  catch { return $false }
}
if (-not (IsReady)) {
  $Exe = Join-Path $env:ProgramFiles 'Docker\Docker\Docker Desktop.exe'
  if (-not (Test-Path $Exe)) { throw 'Docker Engine non disponibile.' }
  Start-Process $Exe
  for ($i=0; $i -lt 60; $i++) { Start-Sleep -Seconds 2; if (IsReady) { break } }
}
if (-not (IsReady)) { throw 'Docker Engine non disponibile. Controlla WSL2.' }
$Existing = @(docker ps -a --filter "name=^/$Name$" --format '{{.Names}}')
if ($Existing -contains $Name) {
  if (-not $ReplaceExisting) {
    $Running = docker inspect -f '{{.State.Running}}' $Name
    if ($Running -eq 'true') { Write-Host 'Container gia attivo: nessuna modifica alle credenziali.' }
    else {
      docker start $Name | Out-Null
      if ($LASTEXITCODE -ne 0) { throw 'docker start non riuscito.' }
      Write-Host 'Container esistente riavviato.'
    }
    Write-Host 'Test: http://127.0.0.1:8765/health'
    return
  }
  Write-Host 'Sostituzione esplicita del SOLO container; volume conservato.'
  docker rm -f $Name | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'Impossibile rimuovere il container.' }
}
if (-not (Test-Path $Dir)) { New-Item -Type Directory -Path $Dir | Out-Null }
if (-not (Test-Path $EnvFile)) {
  $Generator = [Security.Cryptography.RandomNumberGenerator]::Create()
  $Bytes = New-Object byte[] 32
  try { $Generator.GetBytes($Bytes) } finally { $Generator.Dispose() }
  $Token = [BitConverter]::ToString($Bytes).Replace('-', '')
  @("BRIDGE_TOKEN=$Token", 'FATTURA24_ENABLE_WRITES=false') | Set-Content $EnvFile -Encoding Ascii
  Write-Host 'Token locale creato (non mostrato). Scritture disabilitate.'
}
docker pull $Image
if ($LASTEXITCODE -ne 0) { throw 'Download da GHCR fallito.' }
docker volume create fattura24_state | Out-Null
$ArgsDocker = @('run','-d','--name',$Name,'--restart','unless-stopped','--env-file',$EnvFile,'--read-only','--tmpfs','/tmp','--cap-drop','ALL','--security-opt','no-new-privileges','-v','fattura24_state:/data','-p','127.0.0.1:8765:8765',$Image)
docker @ArgsDocker | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'docker run fallito.' }
for ($i=0; $i -lt 30; $i++) {
  try {
    $Response = Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8765/health' -TimeoutSec 3
    if ($Response.StatusCode -eq 200 -and $Response.Content.Trim() -eq 'ok') {
      Write-Host '[OK] MCP locale http://127.0.0.1:8765/mcp'
      exit 0
    }
  } catch { }
  Start-Sleep -Seconds 2
}
throw 'Container avviato, ma health non risponde. docker logs fattura24-mcp'
