from boto3 import client
from elb_load_monitor.alb_alarm_messages import ALBAlarmAction
from elb_load_monitor.alb_alarm_messages import ALBAlarmEvent
from elb_load_monitor.alb_alarm_messages import ALBAlarmStatusMessage
from elb_load_monitor.alb_alarm_messages import CWAlarmState
from elb_load_monitor.elb_listener_rule import ELBListenerRule
from elb_load_monitor import util

import boto3
import json
import logging


logger = logging.getLogger()


class ALBListenerRulesHandler:

    def __init__(
            self, elbv2_client: client, load_balancer_arn: str, elb_listener_arn: str, target_group_arn: str,
            elb_shed_percent: int, max_elb_shed_percent: int, elb_restore_percent: int, shed_mesg_delay_sec: int,
            restore_mesg_delay_sec: int
    ) -> None:
        self.load_balancer_arn = load_balancer_arn
        self.elb_listener_arn = elb_listener_arn
        self.target_group_arn = target_group_arn
        self.elb_shed_percent = elb_shed_percent
        self.max_elb_shed_percent = max_elb_shed_percent
        self.elb_restore_percent = elb_restore_percent
        self.shed_mesg_delay_sec = shed_mesg_delay_sec
        self.restore_mesg_delay_sec = restore_mesg_delay_sec

        try:
            describe_rules_response = elbv2_client.describe_rules(
                ListenerArn=elb_listener_arn
            )

            logger.debug('Listener rules for ' + elb_listener_arn +
                         ': ' + json.dumps(describe_rules_response, default=util.datetime_handler))

            elb_rules_entries = describe_rules_response['Rules']
            self.elb_rules = []

            for elb_rule_entry in elb_rules_entries:
                default_rule = False
                if elb_rule_entry['IsDefault']:
                    # skip the default rule
                    default_rule = True

                rule_actions = elb_rule_entry['Actions']
                rule_arn = elb_rule_entry['RuleArn']

                if len(rule_actions) == 0:
                    logger.warn('No actions defined for rule ' + rule_arn)
                    continue

                action_type = rule_actions[0]['Type']
                if action_type != 'forward':
                    # skip redirect and fixed response actions
                    continue

                elb_listener_rule = ELBListenerRule(
                    rule_arn, elb_listener_arn, default_rule)

                self.elb_rules.append(elb_listener_rule)

                for target_group in rule_actions[0]['ForwardConfig']['TargetGroups']:
                    elb_listener_rule.add_forward_config(
                        target_group['TargetGroupArn'], target_group['Weight'])
        except boto3.ElasticLoadBalancingv2.Client.exceptions.ListenerNotFoundException:
            logger.error(
                'No listener found for listener ARN: ' + elb_listener_arn)

        return

    def handle_alarm(
            self, elbv2_client: client, sqs_client: client, sqs_queue_url: str, alb_alarm_event: ALBAlarmEvent
    ) -> ALBAlarmAction:

        alarm_action = ALBAlarmAction.NONE

        if alb_alarm_event.cw_alarm_state == CWAlarmState.ALARM:
            logger.info('Shedding: ' + str(self.elb_shed_percent) +
                        ' from ' + self.target_group_arn)
            self.shed(elbv2_client, self.target_group_arn,
                      self.elb_shed_percent, self.max_elb_shed_percent)

            if (self.is_sheddable(self.target_group_arn, self.max_elb_shed_percent)):
                alarm_action = ALBAlarmAction.SHED

        elif alb_alarm_event.cw_alarm_state == CWAlarmState.OK:
            alarm_action = ALBAlarmAction.RESTORE
            logger.info('Preparing to restore load to: ' +
                        self.target_group_arn)

        if alarm_action != ALBAlarmAction.NONE:
            self.send_sqs_notification(
                sqs_client, sqs_queue_url, alb_alarm_event.alarm_arn, alb_alarm_event.alarm_name, alarm_action)

        return alarm_action

    def handle_alarm_status_message(
            self, cw_client: client, elbv2_client: client, sqs_client: client,
            alb_alarm_status_message: ALBAlarmStatusMessage
    ) -> ALBAlarmAction:

        alarm_response = cw_client.describe_alarms(
            AlarmNames=[
                alb_alarm_status_message.cw_alarm_name
            ]
        )

        logger.debug('Alarm status for ' + alb_alarm_status_message.cw_alarm_name +
                     ': ' + json.dumps(alarm_response, default=util.datetime_handler))

        if len(alarm_response['MetricAlarms']) == 0:
            logger.error('No alarm with alarm name: ' +
                         alb_alarm_status_message.cw_alarm_name)

            return ALBAlarmAction.NONE

        cw_alarm_state = CWAlarmState[alarm_response['MetricAlarms']
                                      [0]['StateValue']]

        previous_alb_alarm_action = alb_alarm_status_message.alb_alarm_action

        new_alarm_action = ALBAlarmAction.NONE

        if cw_alarm_state == CWAlarmState.ALARM:
            # if current alarm state is ALARM, shed if previous alarm action was SHED
            # otherwise, set the state to SHED and send the message. This will trigger
            # shedding in the next interval
            if previous_alb_alarm_action == ALBAlarmAction.SHED:
                logger.info('Shedding: ' + str(alb_alarm_status_message.elb_shed_percent) +
                            ' from ' + alb_alarm_status_message.target_group_arn)

                self.shed(
                    elbv2_client, alb_alarm_status_message.target_group_arn,
                    alb_alarm_status_message.elb_shed_percent, alb_alarm_status_message.max_elb_shed_percent)

            if (self.is_sheddable(self.target_group_arn, self.max_elb_shed_percent)):
                new_alarm_action = ALBAlarmAction.SHED

            # todo do we need to worry about "over shedding"?

        elif cw_alarm_state == CWAlarmState.OK:
            # if current CWAlarm state is OK, restore if the previous alarm action was RESTORE
            # otherwise, check if we have available capacity to restore and set the state to RESTORE.
            # This will trigger restore  in the next interval
            if previous_alb_alarm_action == ALBAlarmAction.RESTORE:
                logger.info('Restoring: ' + str(alb_alarm_status_message.elb_shed_percent) +
                            ' to ' + alb_alarm_status_message.target_group_arn)

                self.restore(
                    elbv2_client, alb_alarm_status_message.target_group_arn,
                    alb_alarm_status_message.elb_restore_percent)

            if self.is_restorable(alb_alarm_status_message.target_group_arn):
                # if there is more load available, continue to restore
                new_alarm_action = ALBAlarmAction.RESTORE

        elif cw_alarm_state == CWAlarmState.INSUFFICIENT_DATA:
            # if we have insufficient data in the alarm, queue and re-evaulate in
            # the next interval
            logger.info('CloudWatch Alarm: ' + alb_alarm_status_message.cw_alarm_name +
                        ' has insufficient data. Doing nothing and re-queuing: ' + previous_alb_alarm_action.name)

            new_alarm_action = previous_alb_alarm_action

        if new_alarm_action != ALBAlarmAction.NONE:
            self.send_sqs_notification(
                sqs_client, alb_alarm_status_message.sqs_queue_url, alb_alarm_status_message.cw_alarm_arn,
                alb_alarm_status_message.cw_alarm_name, new_alarm_action)

        return new_alarm_action

    def send_sqs_notification(
            self, sqs_client: client, sqs_queue_url: str, cw_alarm_arn: str, cw_alarm_name: str,
            alarm_action: ALBAlarmAction
    ) -> None:
        alb_alarm_status_message = ALBAlarmStatusMessage(
            cw_alarm_arn=cw_alarm_arn, cw_alarm_name=cw_alarm_name,
            load_balancer_arn=self.load_balancer_arn, elb_listener_arn=self.elb_listener_arn,
            target_group_arn=self.target_group_arn, sqs_queue_url=sqs_queue_url,
            shed_mesg_delay_sec=self.shed_mesg_delay_sec, restore_mesg_delay_sec=self.restore_mesg_delay_sec,
            elb_shed_percent=self.elb_shed_percent, max_elb_shed_percent=self.max_elb_shed_percent,
            elb_restore_percent=self.elb_restore_percent,
            alb_alarm_action=alarm_action)

        sqs_delay_sec = self.shed_mesg_delay_sec

        if alarm_action == ALBAlarmAction.RESTORE:
            sqs_delay_sec = self.restore_mesg_delay_sec

        # if we took an action, we want to re-evaluate the decision in 60s
        message_body = json.dumps(alb_alarm_status_message.to_json())
        logger.debug('Queuing message: ' + message_body)

        sqs_client.send_message(
            QueueUrl=sqs_queue_url,
            DelaySeconds=sqs_delay_sec,
            MessageBody=message_body
        )

    def get_elb_rules(self) -> list:
        return self.elb_rules

    def is_restorable(self, source_group_arn: str) -> bool:
        for elb_rule in self.elb_rules:
            if elb_rule.is_restorable(source_group_arn):
                return True

        return False

    def is_sheddable(self, source_group_arn: str, max_shed_weight: int) -> bool:
        for elb_rule in self.elb_rules:
            if elb_rule.is_sheddable(source_group_arn, max_shed_weight):
                return True

        return False

    def restore(self, elbv2_client: client, source_group_arn: str, weight: int) -> None:
        for elb_rule in self.elb_rules:
            elb_rule.restore(source_group_arn, weight)

        for elb_rule in self.elb_rules:
            elb_rule.save(elbv2_client)

        return

    def shed(self, elbv2_client: client, source_group_arn: str, weight: int, max_shed_weight: int) -> None:
        for elb_rule in self.elb_rules:
            elb_rule.shed(source_group_arn, weight, max_shed_weight)

        for elb_rule in self.elb_rules:
            elb_rule.save(elbv2_client)

        return
