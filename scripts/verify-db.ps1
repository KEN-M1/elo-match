$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location $repoRoot
try {
  docker compose exec -T rankkit-postgres psql -U rankkit -d rankkit `
    -c "select version_num from alembic_version;" `
    -c "select table_name from information_schema.tables where table_schema = 'public' order by table_name;"
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
