param(
  [Parameter(Mandatory=$true)]
  [string]$JwtSecretArn,

  [Parameter(Mandatory=$true)]
  [string]$GoogleClientId,

  [Parameter(Mandatory=$true)]
  [string]$GoogleClientSecretArn,

  [Parameter(Mandatory=$true)]
  [string]$AllowedOrigins,

  [string]$ApiImageTag = "main",

  [int]$ApiDesiredCount = 1,

  [Parameter(Mandatory=$true)]
  [string]$ApiCertificateArn,

  [string]$ApiPublicUrl = "https://api.replace-me.example",

  [string]$WebImageTag = "main",

  [int]$WebDesiredCount = 1,

  [string]$WebAppUrl = "https://replace-me.example",

  [Parameter(Mandatory=$true)]
  [string]$WebCertificateArn,

  [string]$AuthRequired = "true",

  [string]$AlarmNotificationTopicArn = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$infraRoot = Join-Path $repoRoot "infra"

Push-Location $infraRoot
try {
  & npx.cmd aws-cdk@2.173.4 deploy RankKitComputeStack `
    --parameters "RankKitComputeStack:JwtSecretArn=$JwtSecretArn" `
    --parameters "RankKitComputeStack:GoogleClientId=$GoogleClientId" `
    --parameters "RankKitComputeStack:GoogleClientSecretArn=$GoogleClientSecretArn" `
    --parameters "RankKitComputeStack:AllowedOrigins=$AllowedOrigins" `
    --parameters "RankKitComputeStack:ApiImageTag=$ApiImageTag" `
    --parameters "RankKitComputeStack:ApiDesiredCount=$ApiDesiredCount" `
    --parameters "RankKitComputeStack:ApiCertificateArn=$ApiCertificateArn" `
    --parameters "RankKitComputeStack:ApiPublicUrl=$ApiPublicUrl" `
    --parameters "RankKitComputeStack:WebImageTag=$WebImageTag" `
    --parameters "RankKitComputeStack:WebDesiredCount=$WebDesiredCount" `
    --parameters "RankKitComputeStack:WebAppUrl=$WebAppUrl" `
    --parameters "RankKitComputeStack:WebCertificateArn=$WebCertificateArn" `
    --parameters "RankKitComputeStack:AuthRequired=$AuthRequired" `
    --parameters "RankKitComputeStack:AlarmNotificationTopicArn=$AlarmNotificationTopicArn" `
    --require-approval never
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
