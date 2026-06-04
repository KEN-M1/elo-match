$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location $repoRoot
try {
  docker compose up -d rankkit-postgres
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
  Write-Host "RankKit Postgres is starting on postgresql://rankkit:rankkit@localhost:5432/rankkit"
} finally {
  Pop-Location
}
