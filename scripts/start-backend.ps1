$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$backendRoot = Join-Path $repoRoot "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
$Port = if ($env:PORT) { $env:PORT } else { "8002" }

if (-not (Test-Path -LiteralPath $python)) {
  throw "Backend virtual environment was not found. Create it and install backend/requirements.txt before starting production runtime."
}

Write-Host "Starting RankKit API on 0.0.0.0:$Port"
Push-Location $backendRoot
try {
  & $python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
}
finally {
  Pop-Location
}
