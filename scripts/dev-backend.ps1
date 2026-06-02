$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$backendRoot = Join-Path $repoRoot "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  Write-Host "Creating backend virtual environment..."
  Push-Location $backendRoot
  python -m venv .venv
  Pop-Location
}

Write-Host "Installing backend dependencies..."
Push-Location $backendRoot
& $python -m pip install -r requirements-dev.txt

Write-Host "Starting RankKit API on http://127.0.0.1:8002"
& $python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
Pop-Location
