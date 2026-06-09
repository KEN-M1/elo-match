from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_elasticloadbalancingv2 as elbv2
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
        load_balancer_security_group: ec2.ISecurityGroup,
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
        self.web_repository = ecr.Repository(
            self,
            "WebRepository",
            repository_name="rankkit-web",
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep the latest 20 web images.",
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
        self.private_subnets = vpc.select_subnets(
            subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
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
        google_client_secret_arn = cdk.CfnParameter(
            self,
            "GoogleClientSecretArn",
            type="String",
            description="Secrets Manager ARN containing the Google OAuth client secret.",
        )
        google_client_secret = secretsmanager.Secret.from_secret_complete_arn(
            self,
            "GoogleClientSecret",
            google_client_secret_arn.value_as_string,
        )
        google_client_id = cdk.CfnParameter(
            self,
            "GoogleClientId",
            type="String",
            description="Google OAuth client ID for the web app.",
        )
        allowed_origins = cdk.CfnParameter(
            self,
            "AllowedOrigins",
            type="String",
            default="https://replace-me.example",
            description="Comma-separated web origins allowed to call the API.",
        )
        api_image_tag = cdk.CfnParameter(
            self,
            "ApiImageTag",
            type="String",
            default="latest",
            description="ECR image tag to run for the API service.",
        )
        api_desired_count = cdk.CfnParameter(
            self,
            "ApiDesiredCount",
            type="Number",
            default=1,
            min_value=0,
            max_value=4,
            description="Number of API tasks to run. Use 0 for first deploy before an image is pushed.",
        )
        api_certificate_arn = cdk.CfnParameter(
            self,
            "ApiCertificateArn",
            type="String",
            description="ACM certificate ARN for the public API load balancer.",
        )
        api_certificate = acm.Certificate.from_certificate_arn(
            self,
            "ApiCertificate",
            api_certificate_arn.value_as_string,
        )
        api_public_url = cdk.CfnParameter(
            self,
            "ApiPublicUrl",
            type="String",
            default="https://api.replace-me.example",
            description="Public HTTPS API origin used by the web app.",
        )
        web_image_tag = cdk.CfnParameter(
            self,
            "WebImageTag",
            type="String",
            default="latest",
            description="ECR image tag to run for the web service.",
        )
        web_desired_count = cdk.CfnParameter(
            self,
            "WebDesiredCount",
            type="Number",
            default=1,
            min_value=0,
            max_value=4,
            description="Number of web tasks to run. Use 0 for first deploy before an image is pushed.",
        )
        web_app_url = cdk.CfnParameter(
            self,
            "WebAppUrl",
            type="String",
            default="https://replace-me.example",
            description="Public web origin used by NextAuth.",
        )
        web_certificate_arn = cdk.CfnParameter(
            self,
            "WebCertificateArn",
            type="String",
            description="ACM certificate ARN for the public web load balancer.",
        )
        web_certificate = acm.Certificate.from_certificate_arn(
            self,
            "WebCertificate",
            web_certificate_arn.value_as_string,
        )
        auth_required = cdk.CfnParameter(
            self,
            "AuthRequired",
            type="String",
            default="true",
            allowed_values=["true", "false"],
            description="Whether the web app should require Google auth for protected routes.",
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
            image=ecs.ContainerImage.from_ecr_repository(
                self.api_repository,
                tag=api_image_tag.value_as_string,
            ),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="api",
                log_group=self.log_group,
            ),
            environment={
                "ALLOWED_ORIGINS": allowed_origins.value_as_string,
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

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "ApiLoadBalancer",
            vpc=vpc,
            internet_facing=True,
            security_group=load_balancer_security_group,
        )
        self.service = ecs.FargateService(
            self,
            "ApiService",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=api_desired_count.value_as_number,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            security_groups=[security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            assign_public_ip=False,
        )
        self.http_listener = self.load_balancer.add_listener(
            "HttpListener",
            port=80,
            open=False,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )
        self.https_listener = self.load_balancer.add_listener(
            "HttpsListener",
            port=443,
            certificates=[api_certificate],
            open=False,
        )
        self.https_listener.add_targets(
            "ApiTargets",
            port=8002,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.service],
            health_check=elbv2.HealthCheck(path="/health", healthy_http_codes="200"),
        )

        self.web_task_definition = ecs.FargateTaskDefinition(
            self,
            "WebTaskDefinition",
            cpu=512,
            memory_limit_mib=1024,
        )
        jwt_secret.grant_read(self.web_task_definition.task_role)
        google_client_secret.grant_read(self.web_task_definition.task_role)
        self.web_task_definition.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[jwt_secret.secret_arn, google_client_secret.secret_arn],
            )
        )

        self.web_log_group = aws_logs.LogGroup(
            self,
            "WebLogGroup",
            log_group_name="/rankkit/web",
            retention=aws_logs.RetentionDays.ONE_MONTH,
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        self.web_container = self.web_task_definition.add_container(
            "WebContainer",
            image=ecs.ContainerImage.from_ecr_repository(
                self.web_repository,
                tag=web_image_tag.value_as_string,
            ),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="web",
                log_group=self.web_log_group,
            ),
            environment={
                "AUTH_REQUIRED": auth_required.value_as_string,
                "GOOGLE_CLIENT_ID": google_client_id.value_as_string,
                "NEXT_PUBLIC_API_URL": api_public_url.value_as_string,
                "NEXTAUTH_URL": web_app_url.value_as_string,
            },
            secrets={
                "GOOGLE_CLIENT_SECRET": ecs.Secret.from_secrets_manager(google_client_secret),
                "NEXTAUTH_SECRET": ecs.Secret.from_secrets_manager(jwt_secret),
            },
            health_check=ecs.HealthCheck(
                command=[
                    "CMD-SHELL",
                    "node -e \"fetch('http://localhost:3000').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))\"",
                ],
                interval=cdk.Duration.seconds(30),
                timeout=cdk.Duration.seconds(5),
                retries=3,
                start_period=cdk.Duration.seconds(30),
            ),
        )
        self.web_container.add_port_mappings(ecs.PortMapping(container_port=3000))

        self.web_load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "WebLoadBalancer",
            vpc=vpc,
            internet_facing=True,
            security_group=load_balancer_security_group,
        )
        self.web_service = ecs.FargateService(
            self,
            "WebService",
            cluster=self.cluster,
            task_definition=self.web_task_definition,
            desired_count=web_desired_count.value_as_number,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
            security_groups=[security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            assign_public_ip=False,
        )
        self.web_http_listener = self.web_load_balancer.add_listener(
            "WebHttpListener",
            port=80,
            open=False,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS",
                port="443",
                permanent=True,
            ),
        )
        self.web_https_listener = self.web_load_balancer.add_listener(
            "WebHttpsListener",
            port=443,
            certificates=[web_certificate],
            open=False,
        )
        self.web_https_listener.add_targets(
            "WebTargets",
            port=3000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.web_service],
            health_check=elbv2.HealthCheck(path="/", healthy_http_codes="200-399"),
        )

        cdk.CfnOutput(self, "ApiRepositoryUri", value=self.api_repository.repository_uri)
        cdk.CfnOutput(self, "WebRepositoryUri", value=self.web_repository.repository_uri)
        cdk.CfnOutput(self, "EcsClusterName", value=self.cluster.cluster_name)
        cdk.CfnOutput(self, "ApiTaskDefinitionArn", value=self.task_definition.task_definition_arn)
        cdk.CfnOutput(self, "WebTaskDefinitionArn", value=self.web_task_definition.task_definition_arn)
        cdk.CfnOutput(self, "ApiServiceName", value=self.service.service_name)
        cdk.CfnOutput(self, "WebServiceName", value=self.web_service.service_name)
        cdk.CfnOutput(self, "LoadBalancerDnsName", value=self.load_balancer.load_balancer_dns_name)
        cdk.CfnOutput(self, "WebLoadBalancerDnsName", value=self.web_load_balancer.load_balancer_dns_name)
        cdk.CfnOutput(
            self,
            "MigrationSubnetIds",
            value=cdk.Fn.join(",", self.private_subnets.subnet_ids),
        )
        cdk.CfnOutput(self, "MigrationSecurityGroupId", value=security_group.security_group_id)
