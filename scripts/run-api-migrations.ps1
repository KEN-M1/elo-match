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
  "--query", "tasks[0].taskArn",
  "--output", "text"
) + $regionArgs

$taskArn = & aws @runTaskArgs
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}
if ([string]::IsNullOrWhiteSpace($taskArn) -or $taskArn -eq "None") {
  throw "AWS ECS did not return a migration task ARN."
}

& aws ecs wait tasks-stopped --cluster $ClusterName --tasks $taskArn @regionArgs
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$describeTaskArgs = @(
  "ecs", "describe-tasks",
  "--cluster", $ClusterName,
  "--tasks", $taskArn,
  "--output", "json"
) + $regionArgs
$taskDescription = & aws @describeTaskArgs | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

$container = $taskDescription.tasks[0].containers | Where-Object { $_.name -eq $ContainerName } | Select-Object -First 1
if ($null -eq $container) {
  throw "Migration container '$ContainerName' was not found in task '$taskArn'."
}

$exitCode = [int]$container.exitCode
if ($exitCode -ne 0) {
  Write-Error "Migration task failed with exit code $exitCode."
  exit $exitCode
}

Write-Host "Migration task completed successfully: $taskArn"
