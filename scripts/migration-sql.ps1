$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$backendRoot = Join-Path $repoRoot "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  Write-Host "Creating backend virtual environment..."
  Push-Location $backendRoot
  try {
    python -m venv .venv
  } finally {
    Pop-Location
  }
}

Push-Location $backendRoot
try {
  & $python -m pip install -r requirements-dev.txt
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
  & $python -m alembic upgrade head --sql
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
