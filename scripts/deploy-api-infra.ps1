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

  [string]$AlarmNotificationTopicArn = "",

  [string]$HostedZoneId = "",

  [string]$HostedZoneName = "",

  [string]$ApiDomainName = "",

  [string]$WebDomainName = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$infraRoot = Join-Path $repoRoot "infra"

function Assert-NotPlaceholder {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Value,

    [Parameter(Mandatory=$true)]
    [string]$Message
  )

  if ([string]::IsNullOrWhiteSpace($Value) -or $Value -match "replace-me") {
    throw $Message
  }
}

Assert-NotPlaceholder `
  -Name "ApiPublicUrl" `
  -Value $ApiPublicUrl `
  -Message "ApiPublicUrl must be set to the deployed API origin."
Assert-NotPlaceholder `
  -Name "WebAppUrl" `
  -Value $WebAppUrl `
  -Message "WebAppUrl must be set to the deployed web origin."

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
    --parameters "RankKitComputeStack:HostedZoneId=$HostedZoneId" `
    --parameters "RankKitComputeStack:HostedZoneName=$HostedZoneName" `
    --parameters "RankKitComputeStack:ApiDomainName=$ApiDomainName" `
    --parameters "RankKitComputeStack:WebDomainName=$WebDomainName" `
    --require-approval never
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
} finally {
  Pop-Location
}
