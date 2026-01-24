import pytest
from elb_load_monitor.alb_alarm_messages import (
    ALBAlarmStatusMessage,
    ALBAlarmEvent,
    ALBAlarmAction,
    CWAlarmState
)


def test_alarm_status_message_to_json():
    """Test message serialization"""
    message = ALBAlarmStatusMessage(
        cw_alarm_arn='arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test',
        cw_alarm_name='test-alarm',
        load_balancer_arn='arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:loadbalancer/app/test/abc',
        elb_listener_arn='arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:listener/app/test/abc/def',
        target_group_arn='arn:aws:elasticloadbalancing:us-east-1:YOUR_ACCOUNT_ID_HERE:targetgroup/test/abc',
        sqs_queue_url='https://sqs.us-east-1.amazonaws.com/YOUR_ACCOUNT_ID_HERE/test',
        shed_mesg_delay_sec=60,
        restore_mesg_delay_sec=120,
        elb_shed_percent=5,
        max_elb_shed_percent=100,
        elb_restore_percent=5,
        alb_alarm_action=ALBAlarmAction.SHED
    )
    
    json_data = message.to_json()
    
    assert json_data['albAlarmAction'] == 'SHED'
    assert json_data['alarmName'] == 'test-alarm'
    assert json_data['elbShedPercent'] == 5


def test_alarm_status_message_from_json():
    """Test message deserialization"""
    json_data = {
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
    
    message = ALBAlarmStatusMessage.from_json(json_data)
    
    assert message.alb_alarm_action == ALBAlarmAction.RESTORE
    assert message.cw_alarm_name == 'test-alarm'
    assert message.elb_shed_percent == 5


def test_alarm_status_message_roundtrip():
    """Test serialize -> deserialize preserves data"""
    original = ALBAlarmStatusMessage(
        cw_alarm_arn='arn:test',
        cw_alarm_name='test',
        load_balancer_arn='arn:lb',
        elb_listener_arn='arn:listener',
        target_group_arn='arn:tg',
        sqs_queue_url='https://sqs',
        shed_mesg_delay_sec=60,
        restore_mesg_delay_sec=120,
        elb_shed_percent=10,
        max_elb_shed_percent=50,
        elb_restore_percent=10,
        alb_alarm_action=ALBAlarmAction.SHED
    )
    
    json_data = original.to_json()
    restored = ALBAlarmStatusMessage.from_json(json_data)
    
    assert restored.cw_alarm_name == original.cw_alarm_name
    assert restored.elb_shed_percent == original.elb_shed_percent
    assert restored.alb_alarm_action == original.alb_alarm_action


def test_alarm_event_creation():
    """Test ALBAlarmEvent initialization"""
    event = ALBAlarmEvent(
        alarm_event_id='event-123',
        alarm_arn='arn:aws:cloudwatch:us-east-1:YOUR_ACCOUNT_ID_HERE:alarm:test',
        alarm_name='test-alarm',
        cw_alarm_state=CWAlarmState.ALARM
    )
    
    assert event.alarm_event_id == 'event-123'
    assert event.alarm_name == 'test-alarm'
    assert event.cw_alarm_state == CWAlarmState.ALARM
