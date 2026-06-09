param(
  [string]$ExpectedAwsAccountId = "",

  [string]$AWSRegion = "",

  [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"

function Test-CommandAvailable {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$InstallHint
  )

  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name is required for production deployment. $InstallHint"
  }
}

function Invoke-CheckedCommand {
  param(
    [Parameter(Mandatory=$true)]
    [scriptblock]$Command,

    [Parameter(Mandatory=$true)]
    [string]$FailureMessage
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw $FailureMessage
  }
}

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$infraRoot = Join-Path $repoRoot "infra"

Test-CommandAvailable -Name "aws" -InstallHint "Install and configure AWS CLI v2."
Test-CommandAvailable -Name "docker" -InstallHint "Install Docker Desktop and make sure the daemon is running."
Test-CommandAvailable -Name "gh" -InstallHint "Install GitHub CLI and authenticate with gh auth login."
Test-CommandAvailable -Name "npx.cmd" -InstallHint "Install Node.js dependencies with pnpm install."

Write-Host "Checking AWS CLI identity..."
$identityJson = aws sts get-caller-identity
if ($LASTEXITCODE -ne 0) {
  throw "AWS CLI could not read caller identity. Check credentials and SSO/session state."
}
$identity = $identityJson | ConvertFrom-Json
Write-Host "AWS CLI identity: $($identity.Account) / $($identity.Arn)"

if ($ExpectedAwsAccountId -and $identity.Account -ne $ExpectedAwsAccountId) {
  throw "AWS CLI is authenticated to account $($identity.Account), expected $ExpectedAwsAccountId."
}

$configuredRegion = $AWSRegion
if (-not $configuredRegion) {
  $configuredRegion = aws configure get region
  if ($LASTEXITCODE -ne 0 -or -not $configuredRegion) {
    throw "AWS region is not configured. Pass -AWSRegion or run aws configure set region <region>."
  }
}
Write-Host "AWS region: $configuredRegion"

Write-Host "Checking Docker..."
Invoke-CheckedCommand `
  -Command { docker version } `
  -FailureMessage "Docker is required for image publishing. Start Docker Desktop and retry."

Write-Host "Checking GitHub Actions status..."
$latestRun = gh run list --branch $Branch --limit 1 --json conclusion,status,databaseId,displayTitle | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $latestRun) {
  throw "GitHub Actions status could not be read. Check gh authentication."
}
if ($latestRun[0].status -ne "completed" -or $latestRun[0].conclusion -ne "success") {
  throw "Latest GitHub Actions run on $Branch is not green: $($latestRun[0].displayTitle) / $($latestRun[0].status) / $($latestRun[0].conclusion)."
}
Write-Host "GitHub Actions latest run is green: $($latestRun[0].databaseId)"

Write-Host "Synthesizing CDK app..."
Push-Location $infraRoot
try {
  Invoke-CheckedCommand `
    -Command { npx.cmd aws-cdk@2.173.4 synth } `
    -FailureMessage "CDK synth failed. Fix infrastructure synthesis before deploying."
} finally {
  Pop-Location
}

Write-Host "Production preflight passed."
