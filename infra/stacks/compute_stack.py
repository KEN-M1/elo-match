from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
import aws_cdk as cdk
from constructs import Construct


class ComputeStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.api_repository = ecr.Repository(
            self,
            "ApiRepository",
            repository_name="rankkit-api",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep the latest 20 API images.",
                    max_image_count=20,
                )
            ],
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        self.cluster = ecs.Cluster(
            self,
            "RankKitCluster",
            vpc=vpc,
            cluster_name="rankkit-cluster",
            container_insights=True,
        )

        cdk.CfnOutput(self, "ApiRepositoryUri", value=self.api_repository.repository_uri)
        cdk.CfnOutput(self, "EcsClusterName", value=self.cluster.cluster_name)
