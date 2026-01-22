from enum import Enum


class CWAlarmState(Enum):
    OK = 0
    ALARM = 1
    INSUFFICIENT_DATA = 2


class ALBAlarmAction(Enum):
    NONE = 1
    SHED = 2
    RESTORE = 3


class ALBAlarmEvent:
    def __init__(self, alarm_event_id: str, alarm_arn: str, alarm_name: str, cw_alarm_state: CWAlarmState) -> None:
        self.alarm_event_id = alarm_event_id
        self.alarm_arn = alarm_arn
        self.alarm_name = alarm_name
        self.cw_alarm_state = cw_alarm_state


class ALBAlarmStatusMessage:

    @classmethod
    def from_json(self, message: dict) -> 'ALBAlarmStatusMessage':
        alb_alarm_status_message = ALBAlarmStatusMessage(
            cw_alarm_arn=message['alarmArn'], cw_alarm_name=message['alarmName'],
            load_balancer_arn=message['loadBalancerArn'], elb_listener_arn=message['elbListenerArn'],
            target_group_arn=message['targetGroupArn'], sqs_queue_url=message['sqsQueueURL'],
            shed_mesg_delay_sec=message['shedMesgDelaySec'], restore_mesg_delay_sec=message['restoreMesgDelaySec'],
            elb_shed_percent=message['elbShedPercent'], max_elb_shed_percent=message['maxElbShedPercent'],
            elb_restore_percent=message['elbRestorePercent'], alb_alarm_action=ALBAlarmAction[message['albAlarmAction']]
        )

        return alb_alarm_status_message

    def __init__(
        self, cw_alarm_arn: str, cw_alarm_name: str, load_balancer_arn: str, elb_listener_arn: str,
        target_group_arn: str, sqs_queue_url: str, shed_mesg_delay_sec: int, restore_mesg_delay_sec: int,
        elb_shed_percent: int, max_elb_shed_percent: int, elb_restore_percent: int, alb_alarm_action: ALBAlarmAction
    ) -> None:
        self.cw_alarm_arn = cw_alarm_arn
        self.cw_alarm_name = cw_alarm_name
        self.load_balancer_arn = load_balancer_arn
        self.elb_listener_arn = elb_listener_arn
        self.elb_shed_percent = elb_shed_percent
        self.max_elb_shed_percent = max_elb_shed_percent
        self.elb_restore_percent = elb_restore_percent
        self.target_group_arn = target_group_arn
        self.sqs_queue_url = sqs_queue_url
        self.shed_mesg_delay_sec = shed_mesg_delay_sec
        self.restore_mesg_delay_sec = restore_mesg_delay_sec
        self.alb_alarm_action = alb_alarm_action

    def to_json(self) -> list:
        message = {
            'albAlarmAction': self.alb_alarm_action.name,
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

        return message
