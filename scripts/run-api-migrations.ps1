param(
  [Parameter(Mandatory=$true)]
  [string]$ClusterName,

  [Parameter(Mandatory=$true)]
  [string]$TaskDefinitionArn,

  [Parameter(Mandatory=$true)]
  [string[]]$SubnetIds,

  [Parameter(Mandatory=$true)]
  [string[]]$SecurityGroupIds,

  [string]$ContainerName = "ApiContainer",

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

$awsCommand = Resolve-CommandPath `
  -Name "aws" `
  -FallbackPaths @("C:\Program Files\Amazon\AWSCLIV2\aws.exe")
if (-not $awsCommand) {
  throw "AWS CLI is required for production migrations. Install and configure AWS CLI v2."
}

$networkConfiguration = @{
  awsvpcConfiguration = @{
    subnets = $SubnetIds
    securityGroups = $SecurityGroupIds
    assignPublicIp = "DISABLED"
  }
} | ConvertTo-Json -Compress -Depth 5

$overrides = @{
  containerOverrides = @(
    @{
      name = $ContainerName
      command = @("python", "-m", "alembic", "upgrade", "head")
    }
  )
} | ConvertTo-Json -Compress -Depth 5

$regionArgs = @()
if (-not [string]::IsNullOrWhiteSpace($AWSRegion)) {
  $regionArgs = @("--region", $AWSRegion)
}

$runTaskArgs = @(
  "ecs", "run-task",
  "--cluster", $ClusterName,
  "--task-definition", $TaskDefinitionArn,
  "--launch-type", "FARGATE",
  "--network-configuration", $networkConfiguration,
  "--overrides", $overrides,
  "--output", "json"
) + $regionArgs

$runTaskResult = & $awsCommand @runTaskArgs | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
$failures = @($runTaskResult.failures)
if ($failures.Count -gt 0) {
  $failureSummary = ($failures | ForEach-Object { "$($_.arn): $($_.reason)" }) -join "; "
  throw "AWS ECS could not start the migration task: $failureSummary"
}

$taskArn = $runTaskResult.tasks[0].taskArn
if ([string]::IsNullOrWhiteSpace($taskArn) -or $taskArn -eq "None") {
  throw "AWS ECS did not return a migration task ARN."
}

& $awsCommand ecs wait tasks-stopped --cluster $ClusterName --tasks $taskArn @regionArgs
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$describeTaskArgs = @(
  "ecs", "describe-tasks",
  "--cluster", $ClusterName,
  "--tasks", $taskArn,
  "--output", "json"
) + $regionArgs
$taskDescription = & $awsCommand @describeTaskArgs | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$task = $taskDescription.tasks[0]
$container = $task.containers | Where-Object { $_.name -eq $ContainerName } | Select-Object -First 1
if ($null -eq $container) {
  throw "Migration container '$ContainerName' was not found in task '$taskArn'."
}

$exitCode = [int]$container.exitCode
if ($exitCode -ne 0) {
  Write-Error "Migration task failed with exit code $exitCode. Stopped reason: $($task.stoppedReason). Container reason: $($container.reason)."
  exit $exitCode
}

Write-Host "Migration task completed successfully: $taskArn"
