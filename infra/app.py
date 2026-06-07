import aws_cdk as cdk

from stacks.compute_stack import ComputeStack
from stacks.database_stack import DatabaseStack
from stacks.network_stack import NetworkStack


app = cdk.App()

network_stack = NetworkStack(app, "RankKitNetworkStack")
database_stack = DatabaseStack(
    app,
    "RankKitDatabaseStack",
    vpc=network_stack.vpc,
    security_group=network_stack.rds_security_group,
)
ComputeStack(
    app,
    "RankKitComputeStack",
    database=database_stack.instance,
    security_group=network_stack.ecs_security_group,
    vpc=network_stack.vpc,
)

app.synth()
