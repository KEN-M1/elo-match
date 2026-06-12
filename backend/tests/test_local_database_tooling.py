import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class LocalDatabaseToolingTests(unittest.TestCase):
    def test_root_scripts_expose_postgres_start_and_migration_commands(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package_json["scripts"]

        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/dev-db.ps1",
            scripts["dev:db"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/migrate-db.ps1",
            scripts["db:migrate"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/migration-sql.ps1",
            scripts["db:sql"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/verify-db.ps1",
            scripts["db:verify"],
        )

    def test_root_scripts_expose_production_runtime_commands(self) -> None:
        package_json = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))
        scripts = package_json["scripts"]

        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/start-backend.ps1",
            scripts["start:backend"],
        )
        self.assertEqual("pnpm --filter @rankkit/web build", scripts["build:web"])
        self.assertEqual("pnpm --filter @rankkit/web start", scripts["start:web"])
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/publish-api-image.ps1",
            scripts["deploy:api-image"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/publish-web-image.ps1",
            scripts["deploy:web-image"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/deploy-api-infra.ps1",
            scripts["deploy:api-infra"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/run-api-migrations.ps1",
            scripts["deploy:api-migrations"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/smoke-production.ps1",
            scripts["deploy:smoke"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/production-preflight.ps1",
            scripts["deploy:preflight"],
        )
        self.assertEqual(
            "docker compose -f compose.production-local.yaml up --build",
            scripts["prod:local"],
        )
        self.assertEqual(
            "docker compose -f compose.production-local.yaml down",
            scripts["prod:local:down"],
        )
        self.assertEqual(
            "powershell -ExecutionPolicy Bypass -File scripts/smoke-production.ps1 -ApiUrl http://localhost:8002 -WebUrl http://localhost:3000",
            scripts["prod:local:smoke"],
        )

        web_package_json = json.loads((REPO_ROOT / "apps" / "web" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("next build", web_package_json["scripts"]["build"])
        self.assertEqual("next start", web_package_json["scripts"]["start"])

    def test_compose_file_defines_rankkit_postgres(self) -> None:
        compose = (REPO_ROOT / "compose.yaml").read_text(encoding="utf-8")

        self.assertIn("rankkit-postgres", compose)
        self.assertIn("POSTGRES_DB: rankkit", compose)
        self.assertIn("POSTGRES_USER: rankkit", compose)
        self.assertIn("POSTGRES_PASSWORD: rankkit", compose)
        self.assertIn("5432:5432", compose)

    def test_local_production_compose_runs_postgres_migrations_api_and_web(self) -> None:
        compose = (REPO_ROOT / "compose.production-local.yaml").read_text(encoding="utf-8")

        for expected in [
            "rankkit-postgres",
            "rankkit-migrate",
            "rankkit-api",
            "rankkit-web",
            "postgres:16-alpine",
            "build:",
            "context: ./backend",
            "context: .",
            "dockerfile: apps/web/Dockerfile",
            "args:",
            "python -m alembic upgrade head",
            "ENVIRONMENT: production",
            "STORE_BACKEND: postgres",
            "DATABASE_HOST: rankkit-postgres",
            "DATABASE_NAME: rankkit",
            "DATABASE_USER: rankkit",
            "DATABASE_PASSWORD: rankkit",
            "JWT_SECRET: local-production-nextauth-secret-32chars",
            "ALLOWED_ORIGINS: http://localhost:3000",
            "NEXT_PUBLIC_API_URL: http://localhost:8002",
            "NEXTAUTH_URL: http://localhost:3000",
            "NEXTAUTH_SECRET: local-production-nextauth-secret-32chars",
            "AUTH_REQUIRED: false",
            "8002:8002",
            "3000:3000",
            "service_completed_successfully",
            "service_healthy",
        ]:
            self.assertIn(expected, compose)

    def test_database_scripts_use_backend_alembic(self) -> None:
        migrate_script = (REPO_ROOT / "scripts" / "migrate-db.ps1").read_text(encoding="utf-8")
        sql_script = (REPO_ROOT / "scripts" / "migration-sql.ps1").read_text(encoding="utf-8")

        self.assertIn("-m alembic upgrade head", migrate_script)
        self.assertIn("-m alembic upgrade head --sql", sql_script)

    def test_database_scripts_propagate_native_command_failures(self) -> None:
        for script_name in ["dev-db.ps1", "migrate-db.ps1", "migration-sql.ps1", "verify-db.ps1"]:
            script = (REPO_ROOT / "scripts" / script_name).read_text(encoding="utf-8")
            self.assertIn("if ($LASTEXITCODE -ne 0)", script)

    def test_backend_start_script_runs_uvicorn_without_reload(self) -> None:
        script = (REPO_ROOT / "scripts" / "start-backend.ps1").read_text(encoding="utf-8")

        self.assertIn("app.main:app", script)
        self.assertIn("--host 0.0.0.0", script)
        self.assertIn("--port $Port", script)
        self.assertNotIn("--reload", script)

    def test_backend_dockerfile_defines_production_api_image(self) -> None:
        dockerfile = (REPO_ROOT / "backend" / "Dockerfile").read_text(encoding="utf-8")
        dockerignore = (REPO_ROOT / "backend" / ".dockerignore").read_text(encoding="utf-8")

        for expected in [
            "FROM python:3.12-slim",
            "pip install --no-cache-dir -r requirements.txt",
            "COPY app ./app",
            "COPY alembic ./alembic",
            "COPY alembic.ini ./alembic.ini",
            "EXPOSE 8002",
            "HEALTHCHECK",
            'CMD ["python", "-m", "uvicorn", "app.main:app"',
            '"--host", "0.0.0.0"',
            '"--port", "8002"',
        ]:
            self.assertIn(expected, dockerfile)
        self.assertNotIn("--reload", dockerfile)

        for expected in [".venv", "__pycache__", "data", ".env", "tests"]:
            self.assertIn(expected, dockerignore)

    def test_web_dockerfile_defines_production_next_image(self) -> None:
        dockerfile = (REPO_ROOT / "apps" / "web" / "Dockerfile").read_text(encoding="utf-8")
        dockerignore = (REPO_ROOT / ".dockerignore").read_text(encoding="utf-8")
        next_config = (REPO_ROOT / "apps" / "web" / "next.config.mjs").read_text(encoding="utf-8")

        for expected in [
            "FROM node:22-alpine AS deps",
            "corepack enable",
            "pnpm install --frozen-lockfile --filter @rankkit/web...",
            "FROM node:22-alpine AS builder",
            "ARG NEXT_PUBLIC_API_URL",
            'RUN test -n "$NEXT_PUBLIC_API_URL"',
            "ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL",
            "pnpm --filter @rankkit/web build",
            "FROM node:22-alpine AS runner",
            "NEXT_TELEMETRY_DISABLED=1",
            "COPY --from=builder --chown=nextjs:nextjs /app/apps/web/.next/standalone ./",
            "COPY --from=builder --chown=nextjs:nextjs /app/apps/web/.next/static ./apps/web/.next/static",
            "EXPOSE 3000",
            'CMD ["node", "apps/web/server.js"]',
        ]:
            self.assertIn(expected, dockerfile)

        for expected in ["node_modules", "apps/web/.next", "backend/.venv", "infra/cdk.out"]:
            self.assertIn(expected, dockerignore)

        self.assertIn('output: "standalone"', next_config)

    def test_publish_api_image_script_builds_tags_and_pushes_ecr_image(self) -> None:
        script = (REPO_ROOT / "scripts" / "publish-api-image.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "[Parameter(Mandatory=$true)]",
            "$RepositoryUri",
            "$ImageTag",
            "Resolve-ImageTag",
            "git rev-parse --short=12 HEAD",
            "Resolve-CommandPath",
            "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe",
            "& $awsCommand ecr get-login-password",
            "docker login --username AWS --password-stdin",
            "docker build --progress=plain -t",
            "docker tag",
            "docker push",
            "if ($LASTEXITCODE -ne 0)",
        ]:
            self.assertIn(expected, script)

    def test_publish_web_image_script_builds_tags_and_pushes_ecr_image(self) -> None:
        script = (REPO_ROOT / "scripts" / "publish-web-image.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "[Parameter(Mandatory=$true)]",
            "$RepositoryUri",
            "$ImageTag",
            "$NextPublicApiUrl",
            "Resolve-ImageTag",
            "git rev-parse --short=12 HEAD",
            "Resolve-CommandPath",
            "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe",
            "& $awsCommand ecr get-login-password",
            "docker login --username AWS --password-stdin",
            "docker build --progress=plain -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=$NextPublicApiUrl -t",
            "docker tag",
            "docker push",
            "if ($LASTEXITCODE -ne 0)",
        ]:
            self.assertIn(expected, script)

    def test_deploy_api_infra_script_passes_cdk_parameters(self) -> None:
        script = (REPO_ROOT / "scripts" / "deploy-api-infra.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "[Parameter(Mandatory=$true)]",
            "$JwtSecretArn",
            "$AllowedOrigins",
            "$ApiImageTag",
            "$ApiDesiredCount",
            "$ApiCertificateArn",
            "$ApiPublicUrl",
            "$WebImageTag",
            "$WebDesiredCount",
            "$WebAppUrl",
            "$WebCertificateArn",
            "Assert-NotPlaceholder",
            "ApiPublicUrl must be set to the deployed API origin.",
            "WebAppUrl must be set to the deployed web origin.",
            "Assert-DeployableImageTag",
            "ApiImageTag cannot be 'main' or 'latest' when ApiDesiredCount is greater than zero.",
            "WebImageTag cannot be 'main' or 'latest' when WebDesiredCount is greater than zero.",
            "$AuthRequired",
            "$AlarmNotificationTopicArn",
            "$HostedZoneId",
            "$HostedZoneName",
            "$ApiDomainName",
            "$WebDomainName",
            "$GoogleClientId",
            "$GoogleClientSecretArn",
            "Push-Location $infraRoot",
            "npx.cmd aws-cdk@2.173.4 deploy RankKitComputeStack",
            '--parameters "RankKitComputeStack:JwtSecretArn=$JwtSecretArn"',
            '--parameters "RankKitComputeStack:AllowedOrigins=$AllowedOrigins"',
            '--parameters "RankKitComputeStack:ApiImageTag=$ApiImageTag"',
            '--parameters "RankKitComputeStack:ApiDesiredCount=$ApiDesiredCount"',
            '--parameters "RankKitComputeStack:ApiCertificateArn=$ApiCertificateArn"',
            '--parameters "RankKitComputeStack:ApiPublicUrl=$ApiPublicUrl"',
            '--parameters "RankKitComputeStack:WebImageTag=$WebImageTag"',
            '--parameters "RankKitComputeStack:WebDesiredCount=$WebDesiredCount"',
            '--parameters "RankKitComputeStack:WebAppUrl=$WebAppUrl"',
            '--parameters "RankKitComputeStack:WebCertificateArn=$WebCertificateArn"',
            '--parameters "RankKitComputeStack:AuthRequired=$AuthRequired"',
            '--parameters "RankKitComputeStack:AlarmNotificationTopicArn=$AlarmNotificationTopicArn"',
            '--parameters "RankKitComputeStack:HostedZoneId=$HostedZoneId"',
            '--parameters "RankKitComputeStack:HostedZoneName=$HostedZoneName"',
            '--parameters "RankKitComputeStack:ApiDomainName=$ApiDomainName"',
            '--parameters "RankKitComputeStack:WebDomainName=$WebDomainName"',
            '--parameters "RankKitComputeStack:GoogleClientId=$GoogleClientId"',
            '--parameters "RankKitComputeStack:GoogleClientSecretArn=$GoogleClientSecretArn"',
            "--require-approval never",
            "if ($LASTEXITCODE -ne 0)",
        ]:
            self.assertIn(expected, script)

    def test_run_api_migrations_script_runs_one_off_ecs_task(self) -> None:
        script = (REPO_ROOT / "scripts" / "run-api-migrations.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "[Parameter(Mandatory=$true)]",
            "$ClusterName",
            "$TaskDefinitionArn",
            "$SubnetIds",
            "$SecurityGroupIds",
            "$ContainerName = \"ApiContainer\"",
            "Resolve-CommandPath",
            "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe",
            '"ecs", "run-task"',
            "& $awsCommand @runTaskArgs",
            "--launch-type",
            "FARGATE",
            "awsvpcConfiguration",
            "assignPublicIp",
            "DISABLED",
            "python",
            "-m",
            "alembic",
            "upgrade",
            "head",
            "& $awsCommand ecs wait tasks-stopped",
            '"ecs", "describe-tasks"',
            "& $awsCommand @describeTaskArgs",
            "exit $exitCode",
        ]:
            self.assertIn(expected, script)

    def test_smoke_production_script_checks_api_and_web_urls(self) -> None:
        script = (REPO_ROOT / "scripts" / "smoke-production.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "[Parameter(Mandatory=$true)]",
            "$ApiUrl",
            "$WebUrl",
            "$MaxAttempts = 30",
            "$DelaySeconds = 5",
            "Invoke-WebRequest",
            "$ApiUrl.TrimEnd('/') + \"/health\"",
            "StatusCode",
            "Write-Host",
            "Start-Sleep",
            "throw",
            "Production smoke passed",
        ]:
            self.assertIn(expected, script)

    def test_production_preflight_script_checks_live_deploy_prerequisites(self) -> None:
        script = (REPO_ROOT / "scripts" / "production-preflight.ps1").read_text(encoding="utf-8")

        for expected in [
            "param(",
            "$ExpectedAwsAccountId",
            "$AWSRegion",
            "Resolve-CommandPath",
            "C:\\Program Files\\Amazon\\AWSCLIV2\\aws.exe",
            "& $awsCommand sts get-caller-identity",
            "& $awsCommand configure get region",
            "git status --short",
            "git rev-parse HEAD",
            "Working tree has uncommitted changes",
            "headSha",
            "does not match local HEAD",
            "docker version",
            "gh run list",
            "npx.cmd aws-cdk@2.173.4 synth",
            "GitHub Actions",
            "AWS CLI",
            "Docker",
            "Production preflight passed",
            "if ($LASTEXITCODE -ne 0)",
        ]:
            self.assertIn(expected, script)

    def test_ci_workflow_verifies_app_build_and_postgres_smoke(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        for expected in [
            "windows-latest",
            "ubuntu-latest",
            "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true",
            "postgres:16-alpine",
            "pnpm test",
            "pnpm run build:web",
            "pnpm run test:e2e",
            "Build backend image",
            "docker build --progress=plain -t rankkit-api ./backend",
            "Run backend image",
            "docker run -d --name rankkit-api-smoke",
            "ENVIRONMENT=production",
            "STORE_BACKEND=postgres",
            "DATABASE_HOST=rankkit-db.example",
            "DATABASE_PASSWORD=ci-db-password",
            "curl --fail http://127.0.0.1:8002/health",
            "python -m alembic upgrade head",
            "python -m app.db.smoke",
            "Web image",
            "docker build --progress=plain -f apps/web/Dockerfile --build-arg NEXT_PUBLIC_API_URL=http://localhost:8002 -t rankkit-web .",
            "docker run -d --name rankkit-web-smoke",
            "NEXT_PUBLIC_API_URL=http://localhost:8002",
            "curl --fail http://127.0.0.1:3001",
            "Local production compose",
            "docker compose -f compose.production-local.yaml config",
            "Start local production compose",
            "docker compose -f compose.production-local.yaml up --build --detach",
            "Smoke local production compose",
            "pwsh -NoLogo -NoProfile -File scripts/smoke-production.ps1 -ApiUrl http://localhost:8002 -WebUrl http://localhost:3000 -MaxAttempts 18 -DelaySeconds 5",
            "Show local production compose logs",
            "docker compose -f compose.production-local.yaml logs",
            "Stop local production compose",
            "docker compose -f compose.production-local.yaml down --volumes",
        ]:
            self.assertIn(expected, workflow)

    def test_verify_db_script_checks_alembic_version_and_tables(self) -> None:
        script = (REPO_ROOT / "scripts" / "verify-db.ps1").read_text(encoding="utf-8")

        self.assertIn("select version_num from alembic_version", script)
        self.assertIn("information_schema.tables", script)


if __name__ == "__main__":
    unittest.main()
