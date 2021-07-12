import logging
from elb_load_monitor.alb_alarm_messages import ALBAlarmEvent
from elb_load_monitor.alb_alarm_messages import ALBAlarmAction
from elb_load_monitor.alb_alarm_messages import ALBAlarmStatusMessage
from elb_load_monitor.alb_alarm_messages import CWAlarmState
from elb_load_monitor.alb_listener_rules_handler import ALBListenerRulesHandler
from unittest.mock import ANY, MagicMock

import json
import pathlib
import unittest

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


class TestALBListenerRulesHandler(unittest.TestCase):

    def setUp(self) -> None:
        self.elbv2_client = MagicMock()
        alb_listener_json = open(pathlib.Path(
            __file__).parent/'test_alb_listener.json', 'r')
        self.elbv2_client.describe_rules = MagicMock(
            return_value=json.loads(alb_listener_json.read()))

        alb_listener_json.close()

        self.cw_client_in_alarm = MagicMock()
        cw_in_alarm_json = open(pathlib.Path(
            __file__).parent/'test_cw_in_alarm.json', 'r')
        self.cw_client_in_alarm.describe_alarms = MagicMock(
            return_value=json.loads(cw_in_alarm_json.read()))

        cw_in_alarm_json.close()

        self.cw_client_ok = MagicMock()
        cw_ok_json = open(pathlib.Path(__file__).parent/'test_cw_ok.json', 'r')
        self.cw_client_ok.describe_alarms = MagicMock(
            return_value=json.loads(cw_ok_json.read()))

        cw_ok_json.close()

        self.cw_alarm_arn = 'arn:aws:cloudwatch:us-east-1:817387504538:alarm:ALB_test'
        self.cw_alarm_name = 'ALB_test'
        self.load_balancer_arn = 'arn:aws:elasticloadbalancing:us-east-1:817387504538:loadbalancer/app/AgentPortalALB/bb6bb42b08f94c0b'
        self.elb_listener_arn = 'arn:aws:elasticloadbalancing:us-east-1:817387504538:listener/app/AgentPortalALB/bb6bb42b08f94c0b/b3784a6b090b3696'
        self.elb_listener_rule_arn = 'arn:aws:elasticloadbalancing:us-east-1:817387504538:listener-rule/app/AgentPortalALB/bb6bb42b08f94c0b/b3784a6b090b3696/9758a586f4921acf'
        self.target_group_arn = 'arn:aws:elasticloadbalancing:us-east-1:817387504538:targetgroup/AppServerATG/090a4ba28ada9d48'
        self.secondary_target_group_arn = 'arn:aws:elasticloadbalancing:us-east-1:817387504538:targetgroup/TestGroup/1566e30628006197'
        self.elb_shed_percent = 20
        self.max_elb_shed_percent = 100
        self.elb_restore_percent = 10
        self.shed_mesg_delay_sec = 60
        self.restore_mesg_delay_sec = 120
        self.sqs_queue_url = 'test_queue_url'

        return

    def test_handle_alarm(self) -> None:
        alb_alarm_event = ALBAlarmEvent(
            alarm_event_id='some_id', alarm_arn=self.cw_alarm_arn,
            alarm_name=self.cw_alarm_name, cw_alarm_state=CWAlarmState.ALARM)

        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alarm_action = alb_listener_rules_handler.handle_alarm(
            self.elbv2_client, sqs_client, self.sqs_queue_url, alb_alarm_event)

        self.assertEqual(alarm_action, ALBAlarmAction.SHED)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 80)
        self.elbv2_client.modify_rule.assert_called_with(
            RuleArn=self.elb_listener_rule_arn, Actions=ANY)

        message_body = {
            'albAlarmAction': 'SHED',
            'alarmArn': alb_alarm_event.alarm_arn,
            'alarmName': alb_alarm_event.alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.shed_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_single_shed(self) -> None:
        alb_alarm_event = ALBAlarmEvent(
            alarm_event_id='some_id', alarm_arn=self.cw_alarm_arn,
            alarm_name=self.cw_alarm_name, cw_alarm_state=CWAlarmState.ALARM)

        sqs_client = MagicMock()

        elb_shed_percent = 20
        max_elb_shed_percent = 10

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            elb_shed_percent, max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alarm_action = alb_listener_rules_handler.handle_alarm(
            self.elbv2_client, sqs_client, self.sqs_queue_url, alb_alarm_event)

        self.assertEqual(alarm_action, ALBAlarmAction.NONE)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 90)
        self.elbv2_client.modify_rule.assert_called_with(
            RuleArn=self.elb_listener_rule_arn, Actions=ANY)

        sqs_client.send_message.assert_not_called()

        return

    def test_handle_alarm_other_states(self) -> None:
        # No other alarm event is expected and thus no actions should be taken
        alb_alarm_event = ALBAlarmEvent(
            alarm_event_id='some_id', alarm_arn=self.cw_alarm_arn,
            alarm_name=self.cw_alarm_name, cw_alarm_state=CWAlarmState.OK)

        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 90
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 10

        alarm_action = alb_listener_rules_handler.handle_alarm(
            self.elbv2_client, sqs_client, self.sqs_queue_url, alb_alarm_event)

        self.assertEqual(alarm_action, ALBAlarmAction.RESTORE)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn], 90)

        self.elbv2_client.modify_rule.assert_not_called()

        message_body = {
            'albAlarmAction': 'RESTORE',
            'alarmArn': alb_alarm_event.alarm_arn,
            'alarmName': alb_alarm_event.alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.restore_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_status_message_shed(self) -> None:
        # previous action was SHED and CW alarm state is in ALARM
        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 90
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 10

        alb_alarm_status_message = ALBAlarmStatusMessage(
            self.cw_alarm_arn, self.cw_alarm_name, self.load_balancer_arn, self.elb_listener_arn,
            self.target_group_arn, self.sqs_queue_url, self.shed_mesg_delay_sec, self.restore_mesg_delay_sec,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent, ALBAlarmAction.SHED
        )

        alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
            self.cw_client_in_alarm, self.elbv2_client, sqs_client, alb_alarm_status_message)

        self.assertEqual(alarm_action, ALBAlarmAction.SHED)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 70)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.secondary_target_group_arn), 30)
        self.elbv2_client.modify_rule.assert_called_with(
            RuleArn=self.elb_listener_rule_arn, Actions=ANY)

        message_body = {
            'albAlarmAction': 'SHED',
            'alarmArn': self.cw_alarm_arn,
            'alarmName': self.cw_alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.shed_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_status_message_shed_previous_restore(self) -> None:
        # previous action was RESTORE but CW alarm state is in ALARM
        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 90
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 10

        alb_alarm_status_message = ALBAlarmStatusMessage(
            self.cw_alarm_arn, self.cw_alarm_name, self.load_balancer_arn, self.elb_listener_arn,
            self.target_group_arn, self.sqs_queue_url, self.shed_mesg_delay_sec, self.restore_mesg_delay_sec,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent, ALBAlarmAction.RESTORE
        )

        alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
            self.cw_client_in_alarm, self.elbv2_client, sqs_client, alb_alarm_status_message)

        self.assertEqual(alarm_action, ALBAlarmAction.SHED)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 90)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.secondary_target_group_arn), 10)
        self.elbv2_client.modify_rule.assert_not_called()

        message_body = {
            'albAlarmAction': 'SHED',
            'alarmArn': self.cw_alarm_arn,
            'alarmName': self.cw_alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.shed_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_status_message_restore(self) -> None:
        # alarm state is OK and previous action was RESTORE
        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 80
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 20

        alb_alarm_status_message = ALBAlarmStatusMessage(
            self.cw_alarm_arn, self.cw_alarm_name, self.load_balancer_arn, self.elb_listener_arn,
            self.target_group_arn, self.sqs_queue_url, self.shed_mesg_delay_sec, self.restore_mesg_delay_sec,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent, ALBAlarmAction.RESTORE
        )

        alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
            self.cw_client_ok, self.elbv2_client, sqs_client, alb_alarm_status_message)

        self.assertEqual(alarm_action, ALBAlarmAction.RESTORE)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 90)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.secondary_target_group_arn), 10)
        self.elbv2_client.modify_rule.assert_called_with(
            RuleArn=self.elb_listener_rule_arn, Actions=ANY)

        message_body = {
            'albAlarmAction': 'RESTORE',
            'alarmArn': self.cw_alarm_arn,
            'alarmName': self.cw_alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.restore_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_status_message_restore_previous_shed(self) -> None:
        # alarm state is OK and previous action was SHED
        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 80
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 20

        alb_alarm_status_message = ALBAlarmStatusMessage(
            self.cw_alarm_arn, self.cw_alarm_name, self.load_balancer_arn, self.elb_listener_arn,
            self.target_group_arn, self.sqs_queue_url, self.shed_mesg_delay_sec, self.restore_mesg_delay_sec,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent, ALBAlarmAction.SHED
        )

        alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
            self.cw_client_ok, self.elbv2_client, sqs_client, alb_alarm_status_message)

        self.assertEqual(alarm_action, ALBAlarmAction.RESTORE)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 80)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.secondary_target_group_arn), 20)
        self.elbv2_client.modify_rule.assert_not_called()

        message_body = {
            'albAlarmAction': 'RESTORE',
            'alarmArn': self.cw_alarm_arn,
            'alarmName': self.cw_alarm_name,
            'elbListenerArn': self.elb_listener_arn,
            'elbShedPercent': self.elb_shed_percent,
            'maxElbShedPercent': self.max_elb_shed_percent,
            'elbRestorePercent': self.elb_restore_percent,
            'loadBalancerArn': self.load_balancer_arn,
            'sqsQueueURL': self.sqs_queue_url,
            'shedMesgDelaySec': self.shed_mesg_delay_sec,
            'restoreMesgDelaySec': self.restore_mesg_delay_sec,
            'targetGroupArn': self.target_group_arn
        }

        sqs_client.send_message.assert_called_with(
            QueueUrl=self.sqs_queue_url, DelaySeconds=self.restore_mesg_delay_sec,
            MessageBody=json.dumps(message_body))

        return

    def test_handle_alarm_status_message_restore_no_remaining_restore(self) -> None:
        # alarm state is OK and previous action was RESTORE.
        # no more loan remains to be restored
        sqs_client = MagicMock()

        alb_listener_rules_handler = ALBListenerRulesHandler(
            self.elbv2_client, self.load_balancer_arn, self.elb_listener_arn, self.target_group_arn,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent,
            self.shed_mesg_delay_sec, self.restore_mesg_delay_sec)

        alb_listener_rules_handler.elb_rules[0].forward_configs[self.target_group_arn] = 90
        alb_listener_rules_handler.elb_rules[0].forward_configs[self.secondary_target_group_arn] = 10

        alb_alarm_status_message = ALBAlarmStatusMessage(
            self.cw_alarm_arn, self.cw_alarm_name, self.load_balancer_arn, self.elb_listener_arn,
            self.target_group_arn, self.sqs_queue_url, self.shed_mesg_delay_sec, self.restore_mesg_delay_sec,
            self.elb_shed_percent, self.max_elb_shed_percent, self.elb_restore_percent, ALBAlarmAction.RESTORE
        )

        alarm_action = alb_listener_rules_handler.handle_alarm_status_message(
            self.cw_client_ok, self.elbv2_client, sqs_client, alb_alarm_status_message)

        self.assertEqual(alarm_action, ALBAlarmAction.NONE)
        self.assertEqual(len(alb_listener_rules_handler.elb_rules), 2)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.target_group_arn), 100)
        self.assertEqual(
            alb_listener_rules_handler.elb_rules[0].forward_configs.get(self.secondary_target_group_arn), 0)
        self.elbv2_client.modify_rule.assert_called_with(
            RuleArn=self.elb_listener_rule_arn, Actions=ANY)

        sqs_client.send_message.assert_not_called()

        return
