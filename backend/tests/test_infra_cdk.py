import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class InfraCdkTests(unittest.TestCase):
    def test_cdk_app_wires_network_stack(self) -> None:
        app_source = (REPO_ROOT / "infra" / "app.py").read_text(encoding="utf-8")

        self.assertIn("cdk.App()", app_source)
        self.assertIn("NetworkStack", app_source)
        self.assertIn("RankKitNetworkStack", app_source)
        self.assertIn("DatabaseStack", app_source)
        self.assertIn("RankKitDatabaseStack", app_source)
        self.assertIn("ComputeStack", app_source)
        self.assertIn("RankKitComputeStack", app_source)
        self.assertIn("network_stack.vpc", app_source)
        self.assertIn("network_stack.rds_security_group", app_source)
        self.assertIn("network_stack.ecs_security_group", app_source)
        self.assertIn("network_stack.alb_security_group", app_source)
        self.assertIn("database_stack.instance", app_source)
        self.assertIn("app.synth()", app_source)

    def test_network_stack_defines_vpc_and_security_groups(self) -> None:
        stack_source = (REPO_ROOT / "infra" / "stacks" / "network_stack.py").read_text(encoding="utf-8")

        for expected in [
            "class NetworkStack(cdk.Stack)",
            "ec2.Vpc",
            "max_azs=2",
            "PRIVATE_WITH_EGRESS",
            "PUBLIC",
            "nat_gateways=1",
            "alb_security_group",
            "ecs_security_group",
            "rds_security_group",
            "cache_security_group",
            "ec2.Port.tcp(80)",
            "ec2.Port.tcp(443)",
            "ec2.Port.tcp(3000)",
            "ec2.Port.tcp(8002)",
            "ec2.Port.tcp(5432)",
            "ec2.Port.tcp(6379)",
            "cdk.CfnOutput",
        ]:
            self.assertIn(expected, stack_source)

    def test_database_stack_defines_rds_postgres(self) -> None:
        stack_source = (REPO_ROOT / "infra" / "stacks" / "database_stack.py").read_text(encoding="utf-8")

        for expected in [
            "class DatabaseStack(cdk.Stack)",
            "rds.DatabaseInstance",
            "rds.DatabaseInstanceEngine.postgres",
            'rds.PostgresEngineVersion.of("16.3", "16")',
            "rds.Credentials.from_generated_secret",
            "instance_type=ec2.InstanceType.of",
            "ec2.InstanceClass.BURSTABLE3",
            "ec2.InstanceSize.MICRO",
            "vpc_subnets=ec2.SubnetSelection",
            "ec2.SubnetType.PRIVATE_WITH_EGRESS",
            "multi_az=False",
            "allocated_storage=20",
            "backup_retention=cdk.Duration.days(7)",
            "removal_policy=cdk.RemovalPolicy.RETAIN",
            "delete_automated_backups=False",
            "CfnOutput",
            "DatabaseEndpoint",
            "DatabaseSecretArn",
        ]:
            self.assertIn(expected, stack_source)

    def test_compute_stack_defines_ecr_repository_and_ecs_cluster(self) -> None:
        stack_source = (REPO_ROOT / "infra" / "stacks" / "compute_stack.py").read_text(encoding="utf-8")

        for expected in [
            "class ComputeStack(cdk.Stack)",
            "ecr.Repository",
            'repository_name="rankkit-api"',
            'repository_name="rankkit-web"',
            "image_scan_on_push=True",
            "lifecycle_rules=[",
            "max_image_count=20",
            "removal_policy=cdk.RemovalPolicy.RETAIN",
            "ecs.Cluster",
            'cluster_name="rankkit-cluster"',
            "container_insights=True",
            "CfnOutput",
            "ApiRepositoryUri",
            "EcsClusterName",
            "ecs.FargateTaskDefinition",
            "cpu=512",
            "memory_limit_mib=1024",
            "ecs.ContainerImage.from_ecr_repository",
            "ecs.Secret.from_secrets_manager",
            "DATABASE_HOST",
            "DATABASE_NAME",
            "DATABASE_USER",
            "DATABASE_PASSWORD",
            "JwtSecretArn",
            "AllowedOrigins",
            "ApiImageTag",
            "ApiDesiredCount",
            "WebImageTag",
            "WebDesiredCount",
            "WebAppUrl",
            "AuthRequired",
            "GoogleClientId",
            "GoogleClientSecretArn",
            "value_as_string",
            "value_as_number",
            "min_value=0",
            "JWT_SECRET",
            "NEXTAUTH_SECRET",
            "NEXTAUTH_URL",
            "NEXT_PUBLIC_API_URL",
            "AUTH_REQUIRED",
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "STORE_BACKEND",
            "ENVIRONMENT",
            "aws_logs.LogGroup",
            "ecs.LogDriver.aws_logs",
            "HealthCheck",
            "urllib.request.urlopen",
            "ApiTaskDefinitionArn",
            "elbv2.ApplicationLoadBalancer",
            "internet_facing=True",
            "ecs.FargateService",
            "desired_count=api_desired_count.value_as_number",
            "desired_count=web_desired_count.value_as_number",
            "assign_public_ip=False",
            "add_listener",
            "add_targets",
            "health_check=elbv2.HealthCheck",
            "LoadBalancerDnsName",
            "WebLoadBalancerDnsName",
            "WebRepositoryUri",
            "WebTaskDefinitionArn",
            "WebServiceName",
            "ApiServiceName",
        ]:
            self.assertIn(expected, stack_source)

    def test_infra_has_cdk_cli_entrypoint(self) -> None:
        cdk_json = (REPO_ROOT / "infra" / "cdk.json").read_text(encoding="utf-8")

        self.assertIn('"app": "python app.py"', cdk_json)
        self.assertIn('"rankkit"', cdk_json)

    def test_ci_synthesizes_cdk_app(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        for expected in [
            "name: CDK synth",
            "working-directory: infra",
            "pip install -r requirements.txt",
            "npx aws-cdk@2.173.4 synth",
        ]:
            self.assertIn(expected, workflow)


if __name__ == "__main__":
    unittest.main()
