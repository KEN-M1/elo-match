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
        self.assertIn("network_stack.vpc", app_source)
        self.assertIn("network_stack.rds_security_group", app_source)
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
