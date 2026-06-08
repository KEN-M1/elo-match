param(
  [Parameter(Mandatory=$true)]
  [string]$JwtSecretArn,

  [Parameter(Mandatory=$true)]
  [string]$AllowedOrigins,

  [string]$ApiImageTag = "main",

  [int]$ApiDesiredCount = 1,

  [string]$WebImageTag = "main",

  [int]$WebDesiredCount = 1,

  [string]$WebAppUrl = "https://replace-me.example",

  [string]$AuthRequired = "true"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$infraRoot = Join-Path $repoRoot "infra"

Push-Location $infraRoot
try {
  & npx.cmd aws-cdk@2.173.4 deploy RankKitComputeStack `
    --parameters "RankKitComputeStack:JwtSecretArn=$JwtSecretArn" `
    --parameters "RankKitComputeStack:AllowedOrigins=$AllowedOrigins" `
    --parameters "RankKitComputeStack:ApiImageTag=$ApiImageTag" `
    --parameters "RankKitComputeStack:ApiDesiredCount=$ApiDesiredCount" `
    --parameters "RankKitComputeStack:WebImageTag=$WebImageTag" `
    --parameters "RankKitComputeStack:WebDesiredCount=$WebDesiredCount" `
    --parameters "RankKitComputeStack:WebAppUrl=$WebAppUrl" `
    --parameters "RankKitComputeStack:AuthRequired=$AuthRequired" `
    --require-approval never
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
