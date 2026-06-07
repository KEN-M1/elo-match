from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as aws_logs
from aws_cdk import aws_rds as rds
from aws_cdk import aws_secretsmanager as secretsmanager
import aws_cdk as cdk
from constructs import Construct


class ComputeStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        database: rds.DatabaseInstance,
        security_group: ec2.ISecurityGroup,
        vpc: ec2.IVpc,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.security_group = security_group

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

        jwt_secret_arn = cdk.CfnParameter(
            self,
            "JwtSecretArn",
            type="String",
            description="Secrets Manager ARN containing the backend JWT secret.",
        )
        jwt_secret = secretsmanager.Secret.from_secret_complete_arn(
            self,
            "JwtSecret",
            jwt_secret_arn.value_as_string,
        )

        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "ApiTaskDefinition",
            cpu=512,
            memory_limit_mib=1024,
        )
        database.secret.grant_read(self.task_definition.task_role)
        jwt_secret.grant_read(self.task_definition.task_role)
        self.task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[database.secret.secret_arn, jwt_secret.secret_arn],
            )
        )

        self.log_group = aws_logs.LogGroup(
            self,
            "ApiLogGroup",
            log_group_name="/rankkit/api",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        self.api_container = self.task_definition.add_container(
            "ApiContainer",
            image=ecs.ContainerImage.from_ecr_repository(self.api_repository),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="api",
                log_group=self.log_group,
            ),
            environment={
                "ALLOWED_ORIGINS": "https://replace-me.example",
                "DATABASE_HOST": database.db_instance_endpoint_address,
                "DATABASE_NAME": "rankkit",
                "DATABASE_PORT": database.db_instance_endpoint_port,
                "ENVIRONMENT": "production",
                "STORE_BACKEND": "postgres",
            },
            secrets={
                "DATABASE_PASSWORD": ecs.Secret.from_secrets_manager(
                    database.secret,
                    field="password",
                ),
                "DATABASE_USER": ecs.Secret.from_secrets_manager(
                    database.secret,
                    field="username",
                ),
                "JWT_SECRET": ecs.Secret.from_secrets_manager(jwt_secret),
            },
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8002/health', timeout=3).read()\"",
                ],
                interval=cdk.Duration.seconds(30),
                timeout=cdk.Duration.seconds(5),
                retries=3,
                start_period=cdk.Duration.seconds(30),
            ),
        )
        self.api_container.add_port_mappings(ecs.PortMapping(container_port=8002))

        cdk.CfnOutput(self, "ApiRepositoryUri", value=self.api_repository.repository_uri)
        cdk.CfnOutput(self, "EcsClusterName", value=self.cluster.cluster_name)
        cdk.CfnOutput(self, "ApiTaskDefinitionArn", value=self.task_definition.task_definition_arn)
