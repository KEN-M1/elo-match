$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$envFile = Join-Path $repoRoot "apps\web\.env.local"

Set-Content -LiteralPath $envFile -Value "NEXT_PUBLIC_API_URL=http://localhost:8002" -Encoding UTF8

Write-Host "Installing web dependencies..."
Push-Location $repoRoot
pnpm.cmd install

Write-Host "Starting RankKit web on http://localhost:3000"
pnpm.cmd --filter @rankkit/web dev
Pop-Location
