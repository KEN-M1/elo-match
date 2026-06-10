param(
  [Parameter(Mandatory=$true)]
  [string]$RepositoryUri,

  [string]$ImageTag = "main",

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

$localImage = "rankkit-api:$ImageTag"
$remoteImage = "$RepositoryUri`:$ImageTag"

Push-Location $repoRoot
try {
  & docker build --progress=plain -t $localImage ./backend
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
