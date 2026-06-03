$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$envFile = Join-Path $repoRoot "apps\web\.env.local"
$apiUrlLine = "NEXT_PUBLIC_API_URL=http://localhost:8002"

if (Test-Path -LiteralPath $envFile) {
  $nextLines = @()
  $updated = $false

  foreach ($line in @(Get-Content -LiteralPath $envFile)) {
    if ($line -match "^NEXT_PUBLIC_API_URL=") {
      $nextLines += $apiUrlLine
      $updated = $true
    } else {
      $nextLines += $line
    }
  }

  if (-not $updated) {
    $nextLines += $apiUrlLine
  }
} else {
  $nextLines = @($apiUrlLine)
}

Set-Content -LiteralPath $envFile -Value $nextLines -Encoding UTF8

Write-Host "Installing web dependencies..."
Push-Location $repoRoot
pnpm.cmd install

Write-Host "Starting RankKit web on http://localhost:3000"
pnpm.cmd --filter @rankkit/web dev
Pop-Location
