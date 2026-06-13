param(
  [Parameter(Mandatory=$true)]
  [string]$JwtSecretArn,

  [Parameter(Mandatory=$true)]
  [string]$GoogleClientId,

  [Parameter(Mandatory=$true)]
  [string]$GoogleClientSecretArn,

  [Parameter(Mandatory=$true)]
  [string]$AllowedOrigins,

  [string]$ApiImageTag = "",

  [int]$ApiDesiredCount = 1,

  [Parameter(Mandatory=$true)]
  [string]$ApiCertificateArn,

  [string]$ApiPublicUrl = "https://api.replace-me.example",

  [string]$WebImageTag = "",

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

function Resolve-ImageTag {
  param(
    [string]$ImageTag
  )

  if (-not [string]::IsNullOrWhiteSpace($ImageTag)) {
    return $ImageTag
  }

  $resolvedTag = git rev-parse --short=12 HEAD
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resolvedTag)) {
    throw "Unable to resolve a default image tag from git. Pass image tags explicitly."
  }

  return $resolvedTag.Trim()
}

function Assert-DeployableImageTag {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Value,

    [Parameter(Mandatory=$true)]
    [int]$DesiredCount,

    [Parameter(Mandatory=$true)]
    [string]$Message
  )

  if ($DesiredCount -le 0) {
    return
  }

  if ([string]::IsNullOrWhiteSpace($Value) -or $Value -in @("main", "latest")) {
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

Push-Location $repoRoot
try {
  $ApiImageTag = Resolve-ImageTag -ImageTag $ApiImageTag
  $WebImageTag = Resolve-ImageTag -ImageTag $WebImageTag
} finally {
  Pop-Location
}

Assert-DeployableImageTag `
  -Name "ApiImageTag" `
  -Value $ApiImageTag `
  -DesiredCount $ApiDesiredCount `
  -Message "ApiImageTag cannot be 'main' or 'latest' when ApiDesiredCount is greater than zero."
Assert-DeployableImageTag `
  -Name "WebImageTag" `
  -Value $WebImageTag `
  -DesiredCount $WebDesiredCount `
  -Message "WebImageTag cannot be 'main' or 'latest' when WebDesiredCount is greater than zero."

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
