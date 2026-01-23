import pytest
from aws_cdk import App
from aws_cdk.assertions import Template, Match
import sys
import os

# Add parent directory to path to import cdk package
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from cdk.alb_monitor_stack import ALBMonitorStack


@pytest.fixture
def template():
    """Create CDK template for testing"""
    app = App(context={'elbTargetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:targetgroup/test/abc'})
    stack = ALBMonitorStack(app, "TestStack")
    return Template.from_stack(stack)


def test_stack_creates_lambda_functions(template):
    """Test stack creates both Lambda functions"""
    template.resource_count_is("AWS::Lambda::Function", 2)


def test_stack_creates_sqs_queues(template):
    """Test stack creates SQS queue and DLQ"""
    template.resource_count_is("AWS::SQS::Queue", 2)


def test_stack_creates_cloudwatch_alarms(template):
    """Test stack creates CloudWatch alarms"""
    template.resource_count_is("AWS::CloudWatch::Alarm", 2)  # ALB alarm + DLQ alarm


def test_stack_creates_eventbridge_rule(template):
    """Test stack creates EventBridge rule"""
    template.resource_count_is("AWS::Events::Rule", 1)


def test_lambda_has_python_313_runtime(template):
    """Test Lambda functions use Python 3.13"""
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.13"
    })


def test_lambda_has_timeout(template):
    """Test Lambda functions have 30 second timeout"""
    template.has_resource_properties("AWS::Lambda::Function", {
        "Timeout": 30
    })


def test_sqs_has_encryption(template):
    """Test SQS queues have encryption enabled"""
    template.has_resource_properties("AWS::SQS::Queue", {
        "SqsManagedSseEnabled": True
    })


def test_sqs_has_dead_letter_queue(template):
    """Test main queue has DLQ configured"""
    template.has_resource_properties("AWS::SQS::Queue", {
        "RedrivePolicy": Match.object_like({
            "maxReceiveCount": 3
        })
    })


def test_iam_roles_have_least_privilege(template):
    """Test IAM roles don't use FullAccess policies"""
    # Check that no managed policies are attached (we use inline policies only)
    template.all_resources_properties("AWS::IAM::Role", {
        "ManagedPolicyArns": Match.absent()
    })


def test_lambda_layer_has_python_313(template):
    """Test Lambda layer is compatible with Python 3.13"""
    template.has_resource_properties("AWS::Lambda::LayerVersion", {
        "CompatibleRuntimes": ["python3.13"]
    })


def test_lambda_has_environment_variables(template):
    """Test Lambda functions have required environment variables"""
    # ALBAlarmLambda should have all config env vars
    template.has_resource_properties("AWS::Lambda::Function", 
        Match.object_like({
            "Environment": {
                "Variables": Match.object_like({
                    "ELB_ARN": Match.any_value(),
                    "ELB_LISTENER_ARN": Match.any_value(),
                    "SQS_QUEUE_URL": Match.any_value(),
                    "ELB_SHED_PERCENT": Match.any_value(),
                    "MAX_ELB_SHED_PERCENT": Match.any_value(),
                    "ELB_RESTORE_PERCENT": Match.any_value(),
                    "SHED_MESG_DELAY_SEC": Match.any_value(),
                    "RESTORE_MESG_DELAY_SEC": Match.any_value()
                })
            }
        })
    )
