import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from elb_load_monitor.alb_listener_rules_handler import ALBListenerRulesHandler
from elb_load_monitor.alb_alarm_messages import ALBAlarmEvent, CWAlarmState, ALBAlarmAction


@pytest.fixture
def mock_clients():
    """Create mock boto3 clients"""
    elbv2 = MagicMock()
    sqs = MagicMock()
    cw = MagicMock()
    return elbv2, sqs, cw


def test_handle_boto3_client_error(mock_clients):
    """Test handling of boto3 ClientError"""
    elbv2, sqs, cw = mock_clients
    
    # Mock describe_rules to raise ClientError
    elbv2.describe_rules.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Access denied'}},
        'DescribeRules'
    )
    
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'arn:tg', 5, 100, 5, 60, 120
    )
    
    # Should handle error gracefully and have empty rules
    assert handler.get_elb_rules() == []


def test_handle_missing_listener():
    """Test handling of missing listener"""
    elbv2 = MagicMock()
    
    # Mock describe_rules to return error
    elbv2.describe_rules.side_effect = Exception("Listener not found")
    
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'arn:tg', 5, 100, 5, 60, 120
    )
    
    # Should handle error and have empty rules
    assert handler.get_elb_rules() == []


def test_handle_invalid_target_group_arn():
    """Test handling of invalid target group ARN"""
    elbv2 = MagicMock()
    elbv2.describe_rules.return_value = {'Rules': []}
    
    # Invalid ARN format
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'invalid-arn', 5, 100, 5, 60, 120
    )
    
    # Should not crash, just have no rules to process
    assert handler.get_elb_rules() == []


def test_sqs_send_failure_handling(mock_clients):
    """Test SQS send failure handling"""
    elbv2, sqs, cw = mock_clients
    
    # Mock rules so handler will try to send SQS message
    elbv2.describe_rules.return_value = {
        'Rules': [{
            'RuleArn': 'arn:rule',
            'IsDefault': False,
            'Actions': [{
                'Type': 'forward',
                'ForwardConfig': {
                    'TargetGroups': [
                        {'TargetGroupArn': 'arn:tg', 'Weight': 100}
                    ]
                }
            }]
        }]
    }
    
    # Mock SQS send_message to raise error
    sqs.send_message.side_effect = ClientError(
        {'Error': {'Code': 'QueueDoesNotExist', 'Message': 'Queue not found'}},
        'SendMessage'
    )
    
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'arn:tg', 5, 100, 5, 60, 120
    )
    
    alarm_event = ALBAlarmEvent('id', 'arn:alarm', 'test', CWAlarmState.ALARM)
    
    # Should raise the SQS error
    with pytest.raises(ClientError):
        handler.handle_alarm(elbv2, sqs, 'https://sqs-url', alarm_event)


def test_handle_alarm_doesnt_exist(mock_clients):
    """Test handling when alarm doesn't exist"""
    elbv2, sqs, cw = mock_clients
    
    elbv2.describe_rules.return_value = {'Rules': []}
    
    # Mock describe_alarms to return empty
    cw.describe_alarms.return_value = {'MetricAlarms': []}
    
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'arn:tg', 5, 100, 5, 60, 120
    )
    
    from elb_load_monitor.alb_alarm_messages import ALBAlarmStatusMessage
    message = ALBAlarmStatusMessage(
        'arn:alarm', 'test', 'arn:lb', 'arn:listener', 'arn:tg',
        'https://sqs', 60, 120, 5, 100, 5, ALBAlarmAction.SHED
    )
    
    # Should return NONE action when alarm doesn't exist
    action = handler.handle_alarm_status_message(cw, elbv2, sqs, message)
    assert action == ALBAlarmAction.NONE


def test_describe_rules_with_no_forward_actions():
    """Test handling rules with no forward actions"""
    elbv2 = MagicMock()
    
    # Mock rules with redirect action (not forward)
    elbv2.describe_rules.return_value = {
        'Rules': [{
            'RuleArn': 'arn:rule',
            'IsDefault': False,
            'Actions': [{
                'Type': 'redirect',
                'RedirectConfig': {}
            }]
        }]
    }
    
    handler = ALBListenerRulesHandler(
        elbv2, 'arn:lb', 'arn:listener', 'arn:tg', 5, 100, 5, 60, 120
    )
    
    # Should skip non-forward rules
    assert len(handler.get_elb_rules()) == 0
