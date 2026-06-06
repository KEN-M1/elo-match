import aws_cdk as cdk

from stacks.database_stack import DatabaseStack
from stacks.network_stack import NetworkStack


app = cdk.App()

network_stack = NetworkStack(app, "RankKitNetworkStack")
DatabaseStack(
    app,
    "RankKitDatabaseStack",
    vpc=network_stack.vpc,
    security_group=network_stack.rds_security_group,
)

app.synth()
