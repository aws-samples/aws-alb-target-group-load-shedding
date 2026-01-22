#!/usr/bin/env python3
import aws_cdk as cdk
from alb_test_stack import AlbTestStack

app = cdk.App()
AlbTestStack(app, "AlbTestStack", env=cdk.Environment(region="us-east-1"))
app.synth()