# Production Release Runbook

This runbook turns the production helpers into a repeatable release sequence. Run it from the
repository root unless a step says otherwise.

## Required Inputs

Collect these values before starting:

- AWS account ID and region.
- API ECR repository URI from `RankKitComputeStack`.
- Web ECR repository URI from `RankKitComputeStack`.
- Release image tag, usually the current Git SHA.
- `JwtSecretArn` for the shared `JWT_SECRET` and `NEXTAUTH_SECRET` value.
- `GoogleClientId`.
- `GoogleClientSecretArn`.
- `AllowedOrigins`, usually the production web origin.
- `ApiCertificateArn` and `WebCertificateArn` in the same region as the load balancers.
- `ApiPublicUrl`, such as `https://api.your-web-app.example`.
- `WebAppUrl`, such as `https://your-web-app.example`.
- Optional `AlarmNotificationTopicArn`, such as
  `arn:aws:sns:us-east-1:123456789012:rankkit-alerts`, for CloudWatch alarm notifications.
- Optional Route53 hosted zone inputs for DNS alias records: `HostedZoneId`, `HostedZoneName`,
  `ApiDomainName`, and `WebDomainName`.
- `EcsClusterName`, `ApiTaskDefinitionArn`, `MigrationSubnetIds`, and `MigrationSecurityGroupId`
  from the compute stack outputs.

## Preflight Verification

Install and configure AWS CLI v2, Docker Desktop, GitHub CLI, Git, Node, pnpm, and Python before
attempting a live deploy. Verify the local branch has a clean working tree and the local HEAD has
passed CI. GitHub Actions is the authoritative Docker image validation path because local Docker can
hang or differ from the Linux runner.

```powershell
git status --short --branch
gh run list --branch main --limit 3
```

Run the production preflight to check the clean working tree, that the latest passing GitHub Actions
run matches local HEAD, AWS CLI identity, AWS region, Docker availability, and CDK synth:

```powershell
pnpm run deploy:preflight -- `
  -ExpectedAwsAccountId 123456789012 `
  -AWSRegion us-east-1
```

Run the same app-level checks locally before cutting a release:

```powershell
pnpm test
pnpm run build:web
pnpm run test:e2e
```

Synthesize the infrastructure template before any deploy:

```powershell
Push-Location infra
npx aws-cdk@2.173.4 synth
Pop-Location
```

Expected output: tests pass, the web build succeeds, Playwright completes, and CDK synth exits
without errors. CDK notices about supported Node versions are informational unless synth fails.
The preflight prints `Production preflight passed.` when the working tree, local HEAD, AWS CLI,
Docker, GitHub Actions, and CDK are ready for the live release sequence.

## Local Production Compose

When live AWS deployment is intentionally deferred, use the local production compose path to run the
same production Dockerfiles against local PostgreSQL:

```powershell
pnpm run prod:local
```

`compose.production-local.yaml` starts PostgreSQL, runs Alembic migrations, starts the FastAPI API
with production runtime validation and the Postgres Store Backend, then starts the Next.js
standalone web container. Open `http://localhost:3000` for the web app and `http://localhost:8002`
for the API. Smoke the local production endpoints with:

```powershell
pnpm run prod:local:smoke
```

Stop the stack with:

```powershell
pnpm run prod:local:down
```

This does not deploy AWS resources or publish images to ECR. Use it to validate the local
production runtime shape while issue `#13` remains deferred.

## First Environment Bootstrap

Use this only for the first deployment into a new environment, or when the ECR repositories do not
exist yet. The goal is to create infrastructure and repositories without starting ECS tasks before
images exist.

```powershell
pnpm run deploy:api-infra -- `
  -JwtSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/jwt `
  -GoogleClientId your-google-client-id `
  -GoogleClientSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/google-client-secret `
  -AllowedOrigins https://your-web-app.example `
  -ApiImageTag bootstrap `
  -ApiDesiredCount 0 `
  -ApiCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/api-certificate-id `
  -ApiPublicUrl https://api.your-web-app.example `
  -WebImageTag bootstrap `
  -WebDesiredCount 0 `
  -WebAppUrl https://your-web-app.example `
  -WebCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/web-certificate-id `
  -AuthRequired true `
  -AlarmNotificationTopicArn arn:aws:sns:us-east-1:123456789012:rankkit-alerts `
  -HostedZoneId Z1234567890ABCDE `
  -HostedZoneName your-web-app.example `
  -ApiDomainName api.your-web-app.example `
  -WebDomainName your-web-app.example
```

Expected output: CloudFormation completes, ECR repository URIs are printed, ECS desired counts
remain zero, Route53 alias records point to the load balancers when hosted zone values are set, and
unhealthy-target alarms publish to the SNS topic when the topic ARN is set.

## Publish Images

Publish both images with the same release tag. When `-ImageTag` is omitted, the publish scripts use
the current Git SHA, which is the recommended release tag.

```powershell
pnpm run deploy:api-image -- `
  -RepositoryUri 123456789012.dkr.ecr.us-east-1.amazonaws.com/rankkit-api
```

```powershell
pnpm run deploy:web-image -- `
  -RepositoryUri 123456789012.dkr.ecr.us-east-1.amazonaws.com/rankkit-web `
  -NextPublicApiUrl https://api.your-web-app.example
```

Expected output: each script logs in to ECR, builds, tags, and pushes the requested image. Stop if
either push fails.

## Run Migrations

Run Alembic migrations with the new API task definition before scaling services to the new image.
Use the private subnet and ECS task security group outputs from the compute stack.

```powershell
pnpm run deploy:api-migrations -- `
  -ClusterName rankkit-cluster `
  -TaskDefinitionArn arn:aws:ecs:us-east-1:123456789012:task-definition/RankKitComputeStackApiTaskDefinition... `
  -SubnetIds subnet-aaa,subnet-bbb `
  -SecurityGroupIds sg-ecs `
  -AWSRegion us-east-1
```

Expected output: the migration task stops with exit code `0`. Stop the release if the task exits
non-zero.

## Roll Out Services

Redeploy compute with running service counts after the images are pushed and migrations pass.

```powershell
pnpm run deploy:api-infra -- `
  -JwtSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/jwt `
  -GoogleClientId your-google-client-id `
  -GoogleClientSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/google-client-secret `
  -AllowedOrigins https://your-web-app.example `
  -ApiImageTag release-git-sha `
  -ApiDesiredCount 1 `
  -ApiCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/api-certificate-id `
  -ApiPublicUrl https://api.your-web-app.example `
  -WebImageTag release-git-sha `
  -WebDesiredCount 1 `
  -WebAppUrl https://your-web-app.example `
  -WebCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/web-certificate-id `
  -AuthRequired true `
  -AlarmNotificationTopicArn arn:aws:sns:us-east-1:123456789012:rankkit-alerts `
  -HostedZoneId Z1234567890ABCDE `
  -HostedZoneName your-web-app.example `
  -ApiDomainName api.your-web-app.example `
  -WebDomainName your-web-app.example
```

Expected output: CloudFormation completes and ECS services stabilize. The deployment circuit breaker
rolls back failed ECS deployments automatically, but still inspect ECS events and target health when
a deploy fails.

## Smoke Check

Run the production smoke check against the public HTTPS origins after ECS services stabilize and DNS
points at the load balancers.

```powershell
pnpm run deploy:smoke -- `
  -ApiUrl https://api.your-web-app.example `
  -WebUrl https://your-web-app.example
```

Expected output: API `/health` and the web root return successful HTTP responses, then the script
prints `Production smoke passed.`

## Rollback

Use the previous image tag when smoke checks fail after a deploy or when CloudWatch target health
alarms fire. Redeploy compute with the previous image tag and the last known good desired counts:

```powershell
pnpm run deploy:api-infra -- `
  -JwtSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/jwt `
  -GoogleClientId your-google-client-id `
  -GoogleClientSecretArn arn:aws:secretsmanager:us-east-1:123456789012:secret:rankkit/google-client-secret `
  -AllowedOrigins https://your-web-app.example `
  -ApiImageTag previous image tag `
  -ApiDesiredCount 1 `
  -ApiCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/api-certificate-id `
  -ApiPublicUrl https://api.your-web-app.example `
  -WebImageTag previous image tag `
  -WebDesiredCount 1 `
  -WebAppUrl https://your-web-app.example `
  -WebCertificateArn arn:aws:acm:us-east-1:123456789012:certificate/web-certificate-id `
  -AuthRequired true `
  -AlarmNotificationTopicArn arn:aws:sns:us-east-1:123456789012:rankkit-alerts `
  -HostedZoneId Z1234567890ABCDE `
  -HostedZoneName your-web-app.example `
  -ApiDomainName api.your-web-app.example `
  -WebDomainName your-web-app.example
```

If migrations are not backward compatible, stop and decide on a database recovery plan before
rolling app code backward. For now, avoid destructive migrations in production releases.

## Failure Handling

- If preflight checks fail, fix locally before publishing images.
- If AWS CLI is missing, install AWS CLI v2, authenticate to the target account, and configure an
  AWS region before retrying the preflight.
- If Docker is unavailable, start Docker Desktop or rely on GitHub Actions for image build proof
  before publishing from a machine with Docker available.
- If GitHub Actions is red, do not release from the branch.
- If image publishing fails, keep desired counts unchanged and retry after correcting ECR, Docker,
  or AWS credential issues.
- If migrations fail, keep the previous running service revision and inspect the stopped ECS task
  logs.
- If service rollout fails, inspect CloudFormation events, ECS service events, target health, and
  the deployment circuit breaker result.
- If DNS does not resolve, verify the hosted zone, Route53 alias records, and certificate domain
  names before changing app settings.
- If alarm notifications do not arrive, verify `AlarmNotificationTopicArn`, SNS topic policy, and
  the topic subscriptions before assuming the alarm did not fire.
- If smoke checks fail, capture the failing URL and status, inspect API/web logs, then roll back to
  the previous image tag when user traffic is at risk.
