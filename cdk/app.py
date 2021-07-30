#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core

from cdk.alb_monitor_stack import ALBMonitorStack
from cdk.alb_cloudwatch_stack import ALBCloudWatchStack

app = core.App()


alb_monitor_stack = ALBMonitorStack(app, "ALBMonitorStack")

alb_cloudwatch_stack = ALBCloudWatchStack(app, 'ALBCloudWatchStack')

app.synth()
