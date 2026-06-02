$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$backendRoot = Join-Path $repoRoot "backend"
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
  throw "Backend virtual environment is missing. Run scripts/dev-backend.ps1 once first."
}

Push-Location $backendRoot
& $python -m unittest discover -s tests -p "test_*.py"
Pop-Location

Push-Location $repoRoot
pnpm.cmd --filter @rankkit/web typecheck
Pop-Location
