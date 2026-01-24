from elb_load_monitor.alb_alarm_messages import CWAlarmState
from elb_load_monitor.alb_alarm_messages import ALBAlarmEvent
from elb_load_monitor.alb_listener_rules_handler import ALBListenerRulesHandler

import boto3
import json
import logging
import os


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, elbv2_client=None, sqs_client=None):
    """
    Lambda handler for ALB alarm events.
    
    Args:
        event: EventBridge event
        context: Lambda context
        elbv2_client: Optional boto3 ELB client (for testing)
        sqs_client: Optional boto3 SQS client (for testing)
    """
    logger.info(json.dumps(event))

    # Initialize clients if not provided (for testing)
    if elbv2_client is None:
        elbv2_client = boto3.client('elbv2')
    if sqs_client is None:
        sqs_client = boto3.client('sqs')

    # Load environment variables
    load_balancer_arn = os.environ.get('ELB_ARN')
    elb_listener_arn = os.environ.get('ELB_LISTENER_ARN')
    sqs_queue_url = os.environ.get('SQS_QUEUE_URL')
    elb_shed_percent = int(os.getenv('ELB_SHED_PERCENT', 5))
    max_elb_shed_percent = int(os.getenv('MAX_ELB_SHED_PERCENT', 100))
    elb_restore_percent = int(os.getenv('ELB_RESTORE_PERCENT', 5))
    shed_mesg_delay_sec = int(os.getenv('SHED_MESG_DELAY_SEC', 60))
    restore_mesg_delay_sec = int(os.getenv('RESTORE_MESG_DELAY_SEC', 60))

    event_type = event['detail-type']
    if event_type == 'Cloudwatch Alarm State Change':
        return {
            "statusCode": 403,
            'message': 'Unsupported event type' + event_type
        }

    alb_alarm_event = ALBAlarmEvent(
        alarm_event_id=event['id'], alarm_arn=event['resources'][0],
        alarm_name=event['detail']['alarmName'],
        cw_alarm_state=CWAlarmState[event['detail']['state']['value']])

    account_id = event['account']
    region = event['region']

    target_group_id = event['detail']['configuration']['metrics'][0]['metricStat']['metric']['dimensions'][
        'TargetGroup']
    target_group_arn = 'arn:aws:elasticloadbalancing:' + \
        region + ':' + account_id + ':' + target_group_id

    alb_listener_rules_handler = ALBListenerRulesHandler(
        elbv2_client, load_balancer_arn, elb_listener_arn, target_group_arn, elb_shed_percent, max_elb_shed_percent,
        elb_restore_percent, shed_mesg_delay_sec, restore_mesg_delay_sec)

    alb_alarm_action = alb_listener_rules_handler.handle_alarm(
        elbv2_client, sqs_client, sqs_queue_url, alb_alarm_event)

    return {
        'statusCode': 200,
        'message': 'Processed alarm:' + alb_alarm_action.name
    }
