import aws_cdk as cdk

from stacks.network_stack import NetworkStack


app = cdk.App()

NetworkStack(app, "RankKitNetworkStack")

app.synth()
