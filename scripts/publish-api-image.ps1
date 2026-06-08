param(
  [Parameter(Mandatory=$true)]
  [string]$RepositoryUri,

  [string]$ImageTag = "main",

  [string]$AWSRegion = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$registry = ($RepositoryUri -split "/")[0]

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

  $password = & aws ecr get-login-password --region $AWSRegion
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
