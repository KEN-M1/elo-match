from aws_cdk import aws_ec2 as ec2
import aws_cdk as cdk
from constructs import Construct


class NetworkStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "RankKitVpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        self.alb_security_group = ec2.SecurityGroup(
            self,
            "AlbSecurityGroup",
            vpc=self.vpc,
            description="Allow public HTTP and HTTPS traffic to the RankKit ALB.",
            allow_all_outbound=True,
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow public HTTP traffic.",
        )
        self.alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(443),
            "Allow public HTTPS traffic.",
        )

        self.ecs_security_group = ec2.SecurityGroup(
            self,
            "EcsSecurityGroup",
            vpc=self.vpc,
            description="Allow RankKit app traffic only from the ALB.",
            allow_all_outbound=True,
        )
        self.ecs_security_group.add_ingress_rule(
            self.alb_security_group,
            ec2.Port.tcp(3000),
            "Allow web traffic from the ALB.",
        )
        self.ecs_security_group.add_ingress_rule(
            self.alb_security_group,
            ec2.Port.tcp(8002),
            "Allow API traffic from the ALB.",
        )

        self.rds_security_group = ec2.SecurityGroup(
            self,
            "RdsSecurityGroup",
            vpc=self.vpc,
            description="Allow PostgreSQL traffic only from RankKit ECS tasks.",
            allow_all_outbound=True,
        )
        self.rds_security_group.add_ingress_rule(
            self.ecs_security_group,
            ec2.Port.tcp(5432),
            "Allow PostgreSQL from ECS tasks.",
        )

        self.cache_security_group = ec2.SecurityGroup(
            self,
            "CacheSecurityGroup",
            vpc=self.vpc,
            description="Allow Redis traffic only from RankKit ECS tasks.",
            allow_all_outbound=True,
        )
        self.cache_security_group.add_ingress_rule(
            self.ecs_security_group,
            ec2.Port.tcp(6379),
            "Allow Redis from ECS tasks.",
        )

        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        cdk.CfnOutput(self, "AlbSecurityGroupId", value=self.alb_security_group.security_group_id)
        cdk.CfnOutput(self, "EcsSecurityGroupId", value=self.ecs_security_group.security_group_id)
        cdk.CfnOutput(self, "RdsSecurityGroupId", value=self.rds_security_group.security_group_id)
        cdk.CfnOutput(self, "CacheSecurityGroupId", value=self.cache_security_group.security_group_id)
