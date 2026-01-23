import pytest
import json
from moto import mock_aws
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import alb_alarm_check_lambda_handler


@pytest.fixture
def sqs_event_shed():
    """SQS event with SHED action"""
    message = {
        'albAlarmAction': 'SHED',
        'alarmArn': 'arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test',
        'alarmName': 'test-alarm',
        'elbListenerArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:listener/app/test/abc/def',
        'elbShedPercent': 5,
        'maxElbShedPercent': 100,
        'elbRestorePercent': 5,
        'loadBalancerArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:loadbalancer/app/test/abc',
        'sqsQueueURL': 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID_HERE/test',
        'shedMesgDelaySec': 60,
        'restoreMesgDelaySec': 120,
        'targetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:targetgroup/test/abc'
    }
    return {
        'Records': [{
            'body': json.dumps(message)
        }]
    }


@pytest.fixture
def lambda_context():
    context = MagicMock()
    context.function_name = "ALBSQSMessageLambda"
    return context


@mock_aws
def test_sqs_message_handler_shed_action(sqs_event_shed, lambda_context):
    """Test SQS message triggers shed action"""
    import boto3
    
    elbv2 = boto3.client('elbv2', region_name='us-east-1')
    sqs = boto3.client('sqs', region_name='us-east-1')
    cw = boto3.client('cloudwatch', region_name='us-east-1')
    
    # Mock describe_rules and describe_alarms
    elbv2.describe_rules = MagicMock(return_value={'Rules': []})
    cw.describe_alarms = MagicMock(return_value={
        'MetricAlarms': [{'StateValue': 'ALARM'}]
    })
    
    response = alb_alarm_check_lambda_handler.lambda_handler(sqs_event_shed, lambda_context, elbv2, sqs, cw)
    
    assert response['statusCode'] == 200
    assert 'New Alarm State' in response['message']


@mock_aws
def test_sqs_message_handler_restore_action(lambda_context):
    """Test SQS message triggers restore action"""
    import boto3
    
    message = {
        'albAlarmAction': 'RESTORE',
        'alarmArn': 'arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test',
        'alarmName': 'test-alarm',
        'elbListenerArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:listener/app/test/abc/def',
        'elbShedPercent': 5,
        'maxElbShedPercent': 100,
        'elbRestorePercent': 5,
        'loadBalancerArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:loadbalancer/app/test/abc',
        'sqsQueueURL': 'https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID_HERE/test',
        'shedMesgDelaySec': 60,
        'restoreMesgDelaySec': 120,
        'targetGroupArn': 'arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:targetgroup/test/abc'
    }
    event = {'Records': [{'body': json.dumps(message)}]}
    
    elbv2 = boto3.client('elbv2', region_name='us-east-1')
    sqs = boto3.client('sqs', region_name='us-east-1')
    cw = boto3.client('cloudwatch', region_name='us-east-1')
    
    elbv2.describe_rules = MagicMock(return_value={'Rules': []})
    cw.describe_alarms = MagicMock(return_value={
        'MetricAlarms': [{'StateValue': 'OK'}]
    })
    
    response = alb_alarm_check_lambda_handler.lambda_handler(event, lambda_context, elbv2, sqs, cw)
    
    assert response['statusCode'] == 200


def test_sqs_message_handler_empty_records(lambda_context):
    """Test handler handles empty SQS records"""
    event = {'Records': []}
    
    response = alb_alarm_check_lambda_handler.lambda_handler(event, lambda_context)
    
    assert response is None  # Handler returns early


def test_sqs_message_handler_malformed_message(lambda_context):
    """Test handler handles malformed JSON"""
    event = {'Records': [{'body': 'not valid json'}]}
    
    with pytest.raises(json.JSONDecodeError):
        alb_alarm_check_lambda_handler.lambda_handler(event, lambda_context)
