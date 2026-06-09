import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ReadmeDocsTests(unittest.TestCase):
    def test_readme_documents_local_demo_and_database_smoke_paths(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in [
            "## Demo Readiness Checklist",
            "http://localhost:3000/demo",
            "pnpm run test:e2e",
            "## Google OAuth Setup",
            "## Production Runtime Commands",
            "pnpm run start:backend",
            "pnpm run build:web",
            "pnpm run start:web",
            "## Backend Container Image",
            "docker build -t rankkit-api ./backend",
            "pnpm run deploy:api-image",
            "## Web Container Image",
            "docker build -f apps/web/Dockerfile -t rankkit-web .",
            "pnpm run deploy:web-image",
            "## AWS CDK Infrastructure",
            "RankKitDatabaseStack",
            "RankKitComputeStack",
            "application load balancer",
            "Fargate service",
            "AllowedOrigins",
            "ApiImageTag",
            "ApiDesiredCount",
            "ApiCertificateArn",
            "ApiPublicUrl",
            "WebImageTag",
            "WebDesiredCount",
            "WebAppUrl",
            "WebCertificateArn",
            "GoogleClientId",
            "GoogleClientSecretArn",
            "AlarmNotificationTopicArn",
            "HostedZoneId",
            "HostedZoneName",
            "ApiDomainName",
            "WebDomainName",
            "ACM certificates",
            "deployment circuit breakers",
            "CloudWatch alarms",
            "/api/auth/callback/google",
            "-ApiDesiredCount 0",
            "-WebDesiredCount 0",
            "cdk synth",
            "pnpm run deploy:api-infra",
            "pnpm run deploy:preflight",
            "## Production Database Migrations",
            "pnpm run deploy:api-migrations",
            "## Production Smoke Check",
            "pnpm run deploy:smoke",
            "MigrationSubnetIds",
            "MigrationSecurityGroupId",
            "## CI Verification",
            "Postgres smoke",
            "backend Docker image",
            "web image job",
            "CDK synth",
            "## Postgres Adapter Smoke",
            "pnpm run db:smoke",
            "DISPUTED",
            "REJECTED",
        ]:
            self.assertIn(expected, readme)

    def test_env_example_documents_local_and_production_runtime_settings(self) -> None:
        env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

        for expected in [
            "ENVIRONMENT=local",
            "STORE_BACKEND=local",
            "NEXT_PUBLIC_API_URL=http://localhost:8002",
            "AUTH_REQUIRED=false",
            "ENVIRONMENT=production",
            "STORE_BACKEND=postgres",
            "ALLOWED_ORIGINS=https://your-web-app.example",
            "DATABASE_HOST=your-rds-endpoint.example",
            "DATABASE_PASSWORD=replace-with-rds-secret-password",
            "JWT_SECRET=replace-with-the-same-32-character-or-longer-secret-used-by-nextauth",
            "NEXTAUTH_SECRET=replace-with-the-same-32-character-or-longer-secret-used-by-backend",
            "AUTH_REQUIRED=true",
            "GOOGLE_CLIENT_ID=your-google-client-id",
            "GOOGLE_CLIENT_SECRET=your-google-client-secret",
        ]:
            self.assertIn(expected, env_example)

    def test_production_release_runbook_documents_repeatable_deploy_flow(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        runbook = (REPO_ROOT / "docs" / "production-release-runbook.md").read_text(encoding="utf-8")

        self.assertIn("docs/production-release-runbook.md", readme)

        for expected in [
            "# Production Release Runbook",
            "## Required Inputs",
            "## Preflight Verification",
            "pnpm test",
            "pnpm run build:web",
            "pnpm run test:e2e",
            "npx aws-cdk@2.173.4 synth",
            "pnpm run deploy:preflight",
            "AWS CLI",
            "Docker",
            "## First Environment Bootstrap",
            "-ApiDesiredCount 0",
            "-WebDesiredCount 0",
            "## Publish Images",
            "pnpm run deploy:api-image",
            "pnpm run deploy:web-image",
            "## Run Migrations",
            "pnpm run deploy:api-migrations",
            "## Roll Out Services",
            "-ApiDesiredCount 1",
            "-WebDesiredCount 1",
            "## Smoke Check",
            "pnpm run deploy:smoke",
            "## Rollback",
            "previous image tag",
            "deployment circuit breaker",
            "## Failure Handling",
            "GitHub Actions",
            "AlarmNotificationTopicArn",
            "arn:aws:sns:us-east-1:123456789012:rankkit-alerts",
            "hosted zone",
            "api.your-web-app.example",
        ]:
            self.assertIn(expected, runbook)


if __name__ == "__main__":
    unittest.main()
