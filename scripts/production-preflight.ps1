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

function Resolve-CommandPath {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [string[]]$FallbackPaths = @()
  )

  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if ($command) {
    return $command.Source
  }

  foreach ($path in $FallbackPaths) {
    if (Test-Path -LiteralPath $path) {
      return $path
    }
  }

  return $null
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

$awsCommand = Resolve-CommandPath `
  -Name "aws" `
  -FallbackPaths @("C:\Program Files\Amazon\AWSCLIV2\aws.exe")
if (-not $awsCommand) {
  throw "AWS CLI is required for production deployment. Install and configure AWS CLI v2."
}
Test-CommandAvailable -Name "docker" -InstallHint "Install Docker Desktop and make sure the daemon is running."
Test-CommandAvailable -Name "gh" -InstallHint "Install GitHub CLI and authenticate with gh auth login."
Test-CommandAvailable -Name "npx.cmd" -InstallHint "Install Node.js dependencies with pnpm install."

Write-Host "Checking AWS CLI identity..."
$identityJson = & $awsCommand sts get-caller-identity
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
  $configuredRegion = & $awsCommand configure get region
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
