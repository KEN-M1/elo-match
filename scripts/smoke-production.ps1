param(
  [Parameter(Mandatory=$true)]
  [string]$ApiUrl,

  [Parameter(Mandatory=$true)]
  [string]$WebUrl,

  [int]$MaxAttempts = 30,

  [int]$DelaySeconds = 5
)

$ErrorActionPreference = "Stop"

function Test-RankKitEndpoint {
  param(
    [Parameter(Mandatory=$true)]
    [string]$Name,

    [Parameter(Mandatory=$true)]
    [string]$Url
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
        Write-Host "$Name smoke passed with status $($response.StatusCode): $Url"
        return $response
      }
      Write-Host "$Name smoke attempt $attempt returned status $($response.StatusCode): $Url"
    } catch {
      Write-Host "$Name smoke attempt $attempt failed: $($_.Exception.Message)"
    }

    if ($attempt -lt $MaxAttempts) {
      Start-Sleep -Seconds $DelaySeconds
    }
  }

  throw "$Name smoke failed after $MaxAttempts attempts: $Url"
}

$apiHealthUrl = $ApiUrl.TrimEnd('/') + "/health"
$webRootUrl = $WebUrl.TrimEnd('/')

$apiResponse = Test-RankKitEndpoint -Name "API health" -Url $apiHealthUrl
$apiHealth = $apiResponse.Content | ConvertFrom-Json
if ($apiHealth.status -ne "ok") {
  throw "API health response did not report status ok: $($apiResponse.Content)"
}
Test-RankKitEndpoint -Name "Web root" -Url $webRootUrl

Write-Host "Production smoke passed."
