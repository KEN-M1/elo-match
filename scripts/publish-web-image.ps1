param(
  [Parameter(Mandatory=$true)]
  [string]$RepositoryUri,

  [Parameter(Mandatory=$true)]
  [string]$NextPublicApiUrl,

  [string]$ImageTag = "",

  [string]$AWSRegion = ""
)

$ErrorActionPreference = "Stop"

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

function Resolve-ImageTag {
  param(
    [string]$ImageTag
  )

  if (-not [string]::IsNullOrWhiteSpace($ImageTag)) {
    return $ImageTag
  }

  $resolvedTag = git rev-parse --short=12 HEAD
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resolvedTag)) {
    throw "Unable to resolve a default image tag from git. Pass -ImageTag explicitly."
  }

  return $resolvedTag.Trim()
}

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$registry = ($RepositoryUri -split "/")[0]
$awsCommand = Resolve-CommandPath `
  -Name "aws" `
  -FallbackPaths @("C:\Program Files\Amazon\AWSCLIV2\aws.exe")
if (-not $awsCommand) {
  throw "AWS CLI is required for image publishing. Install and configure AWS CLI v2."
}

if ([string]::IsNullOrWhiteSpace($AWSRegion)) {
  if ($registry -match "\.ecr\.([a-z0-9-]+)\.amazonaws\.com") {
    $AWSRegion = $Matches[1]
  } else {
    throw "Unable to infer AWS region from repository URI. Pass -AWSRegion explicitly."
  }
}

Push-Location $repoRoot
try {
  $ImageTag = Resolve-ImageTag -ImageTag $ImageTag
  $localImage = "rankkit-web:$ImageTag"
  $remoteImage = "$RepositoryUri`:$ImageTag"

  & docker build --progress=plain -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=$NextPublicApiUrl -t $localImage .
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  $password = & $awsCommand ecr get-login-password --region $AWSRegion
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }
  $password | docker login --username AWS --password-stdin $registry
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  & docker tag $localImage $remoteImage
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  & docker push $remoteImage
  if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
  }

  Write-Host "Published $remoteImage"
} finally {
  Pop-Location
}
