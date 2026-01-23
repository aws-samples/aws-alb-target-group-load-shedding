from aws_cdk import (
    Stack,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct

class AlbTestStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import existing VPC and subnets
        vpc = ec2.Vpc.from_lookup(self, "VPC", vpc_id="vpc-0fe561c883f7f8108")
        subnets = [
            ec2.Subnet.from_subnet_id(self, "Subnet1", "subnet-089b7585d49b2104f"),
            ec2.Subnet.from_subnet_id(self, "Subnet2", "subnet-04ac974c6e9804184")
        ]
        
        # Create ALB
        alb = elbv2.ApplicationLoadBalancer(
            self, "ALB",
            load_balancer_name="alb-test-loadshed",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=subnets),
            internet_facing=True
        )
        
        # Create target groups
        ptg = elbv2.ApplicationTargetGroup(
            self, "PTG",
            target_group_name="alb-test-ptg",
            port=80,
            vpc=vpc
        )
        
        stg = elbv2.ApplicationTargetGroup(
            self, "STG", 
            target_group_name="alb-test-stg",
            port=80,
            vpc=vpc
        )
        
        # Create listener with weighted routing
        listener = alb.add_listener(
            "Listener",
            port=80,
            default_action=elbv2.ListenerAction.weighted_target_groups([
                elbv2.WeightedTargetGroup(target_group=ptg, weight=100),
                elbv2.WeightedTargetGroup(target_group=stg, weight=0)
            ])
        )
        
        # Add tags
        tags = {"Purpose": "CDK-v2-Testing", "AutoDelete": "true"}
        for resource in [alb, ptg, stg]:
            for key, value in tags.items():
                resource.node.add_metadata(key, value)
        
        # Outputs
        CfnOutput(self, "ALB_ARN", value=alb.load_balancer_arn)
        CfnOutput(self, "Listener_ARN", value=listener.listener_arn)
        CfnOutput(self, "PTG_ARN", value=ptg.target_group_arn)