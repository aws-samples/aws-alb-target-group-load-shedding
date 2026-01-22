#!/usr/bin/env python3
import os
from aws_cdk import App
from cdk.alb_monitor_stack import ALBMonitorStack

app = App()
alb_monitor_stack = ALBMonitorStack(app, "ALBMonitorStack")
app.synth()
