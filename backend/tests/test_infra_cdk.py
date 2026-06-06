import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class InfraCdkTests(unittest.TestCase):
    def test_cdk_app_wires_network_stack(self) -> None:
        app_source = (REPO_ROOT / "infra" / "app.py").read_text(encoding="utf-8")

        self.assertIn("cdk.App()", app_source)
        self.assertIn("NetworkStack", app_source)
        self.assertIn("RankKitNetworkStack", app_source)
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

    def test_infra_has_cdk_cli_entrypoint(self) -> None:
        cdk_json = (REPO_ROOT / "infra" / "cdk.json").read_text(encoding="utf-8")

        self.assertIn('"app": "python app.py"', cdk_json)
        self.assertIn('"rankkit"', cdk_json)


if __name__ == "__main__":
    unittest.main()
