$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$dataFile = Join-Path $repoRoot "backend\data\rankkit-local.json"

if (Test-Path -LiteralPath $dataFile) {
  Remove-Item -LiteralPath $dataFile -Force
  Write-Host "Deleted $dataFile"
} else {
  Write-Host "No local RankKit data file found."
}
