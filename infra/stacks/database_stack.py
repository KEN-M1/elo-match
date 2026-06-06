from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
import aws_cdk as cdk
from constructs import Construct


class DatabaseStack(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.instance = rds.DatabaseInstance(
            self,
            "RankKitPostgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.of("16.3", "16")
            ),
            credentials=rds.Credentials.from_generated_secret("rankkit"),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[security_group],
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO,
            ),
            allocated_storage=20,
            database_name="rankkit",
            multi_az=False,
            backup_retention=cdk.Duration.days(7),
            deletion_protection=True,
            delete_automated_backups=False,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        cdk.CfnOutput(self, "DatabaseEndpoint", value=self.instance.db_instance_endpoint_address)
        cdk.CfnOutput(self, "DatabasePort", value=self.instance.db_instance_endpoint_port)
        cdk.CfnOutput(self, "DatabaseSecretArn", value=self.instance.secret.secret_arn)
