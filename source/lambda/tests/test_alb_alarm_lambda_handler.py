import pytest
import json
import os
from moto import mock_aws
from unittest.mock import MagicMock
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import alb_alarm_lambda_handler


@pytest.fixture
def lambda_env_vars(monkeypatch):
    """Set Lambda environment variables"""
    monkeypatch.setenv('ELB_ARN', 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:loadbalancer/app/test/abc')
    monkeypatch.setenv('ELB_LISTENER_ARN', 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:listener/app/test/abc/def')
    monkeypatch.setenv('SQS_QUEUE_URL', 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID_HERE/test')
    monkeypatch.setenv('ELB_SHED_PERCENT', '5')
    monkeypatch.setenv('MAX_ELB_SHED_PERCENT', '100')
    monkeypatch.setenv('ELB_RESTORE_PERCENT', '5')
    monkeypatch.setenv('SHED_MESG_DELAY_SEC', '60')
    monkeypatch.setenv('RESTORE_MESG_DELAY_SEC', '120')


@pytest.fixture
def alarm_event():
    return {
        'id': 'test-id',
        'detail-type': 'CloudWatch Alarm State Change',
        'resources': ['arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test'],
        'detail': {
            'alarmName': 'test',
            'state': {'value': 'ALARM'},
            'configuration': {
                'metrics': [{
                    'metricStat': {
                        'metric': {
                            'dimensions': {'TargetGroup': 'targetgroup/test/abc'}
                        }
                    }
                }]
            }
        },
        'account': 'YOUR_ACCOUNT_ID_HERE',
        'region': 'us-east-1'
    }


@pytest.fixture
def lambda_context():
    context = MagicMock()
    context.function_name = "ALBAlarmLambda"
    return context


@mock_aws
def test_lambda_handler_alarm_state(alarm_event, lambda_context, lambda_env_vars):
    """Test handler processes ALARM state"""
    import boto3
    
    # Create mocked clients
    elbv2 = boto3.client('elbv2', region_name='us-east-1')
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    # Mock describe_rules
    elbv2.describe_rules = MagicMock(return_value={'Rules': []})
    
    response = alb_alarm_lambda_handler.lambda_handler(alarm_event, lambda_context, elbv2, sqs)
    
    assert response['statusCode'] == 200
    assert 'Processed alarm' in response['message']


def test_lambda_handler_invalid_event_type(lambda_context, lambda_env_vars):
    """Test handler rejects invalid event types"""
    event = {
        'detail-type': 'Cloudwatch Alarm State Change',  # Wrong case
        'detail': {'alarmName': 'test', 'state': {'value': 'ALARM'}},
        'resources': ['arn'],
        'account': 'YOUR_ACCOUNT_ID_HERE',
        'region': 'us-east-1'
    }
    
    response = alb_alarm_lambda_handler.lambda_handler(event, lambda_context)
    
    assert response['statusCode'] == 403
    assert 'Unsupported event type' in response['message']


@mock_aws
def test_lambda_handler_ok_state(lambda_context, lambda_env_vars):
    """Test handler processes OK state"""
    import boto3
    
    event = {
        'id': 'test-id',
        'detail-type': 'CloudWatch Alarm State Change',
        'resources': ['arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test'],
        'detail': {
            'alarmName': 'test',
            'state': {'value': 'OK'},
            'configuration': {
                'metrics': [{
                    'metricStat': {
                        'metric': {
                            'dimensions': {'TargetGroup': 'targetgroup/test/abc'}
                        }
                    }
                }]
            }
        },
        'account': 'YOUR_ACCOUNT_ID_HERE',
        'region': 'us-east-1'
    }
    
    elbv2 = boto3.client('elbv2', region_name='us-east-1')
    sqs = boto3.client('sqs', region_name='us-east-1')
    
    # Create SQS queue for the test
    queue = sqs.create_queue(QueueName='test-queue')
    os.environ['SQS_QUEUE_URL'] = queue['QueueUrl']
    
    elbv2.describe_rules = MagicMock(return_value={'Rules': []})
    
    response = alb_alarm_lambda_handler.lambda_handler(event, lambda_context, elbv2, sqs)
    
    assert response['statusCode'] == 200


