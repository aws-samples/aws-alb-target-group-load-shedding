import boto3
import json
import logging

from elb_load_monitor.alb_alarm_messages import ALBAlarmStatusMessage
from elb_load_monitor.alb_listener_rules_handler import ALBAlarmAction, ALBListenerRulesHandler
from elb_load_monitor import util


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context, elbv2_client=None, sqs_client=None, cw_client=None):
    """
    Lambda handler for SQS messages.
    
    Args:
        event: SQS event
        context: Lambda context
        elbv2_client: Optional boto3 ELB client (for testing)
        sqs_client: Optional boto3 SQS client (for testing)
        cw_client: Optional boto3 CloudWatch client (for testing)
    """
    logger.info(json.dumps(event, default=util.datetime_handler))

    # Initialize clients if not provided (for testing)
    if elbv2_client is None:
        elbv2_client = boto3.client('elbv2')
    if sqs_client is None:
        sqs_client = boto3.client('sqs')
    if cw_client is None:
        cw_client = boto3.client('cloudwatch')

    if len(event['Records']) == 0:
        logger.warning('No SQS message: ')
        return

    message = event['Records'][0]['body']

    alb_alarm_status_message = ALBAlarmStatusMessage.from_json(
        json.loads(message))

    alb_listener_rules_handler = ALBListenerRulesHandler(
        elbv2_client, alb_alarm_status_message.load_balancer_arn,
        alb_alarm_status_message.elb_listener_arn, alb_alarm_status_message.target_group_arn,
        alb_alarm_status_message.elb_shed_percent, alb_alarm_status_message.max_elb_shed_percent,
        alb_alarm_status_message.elb_restore_percent, alb_alarm_status_message.shed_mesg_delay_sec,
        alb_alarm_status_message.restore_mesg_delay_sec)

    alb_alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
        cw_client, elbv2_client, sqs_client, alb_alarm_status_message)

    return {
        'statusCode': 200,
        'message': 'New Alarm State:' + alb_alarm_action.name
    }
