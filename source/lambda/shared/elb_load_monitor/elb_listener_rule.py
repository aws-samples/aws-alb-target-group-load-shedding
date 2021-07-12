from re import S
from boto3 import client
from builtins import divmod

import json
import logging

from elb_load_monitor import util

logger = logging.getLogger()


class ELBListenerRule:
    def __init__(self, elb_rule_arn: str, elb_listener_arn: str, default_rule: bool) -> None:
        self.elb_rule_arn = elb_rule_arn
        self.elb_listener_arn = elb_listener_arn
        self.default_rule = default_rule
        self.forward_configs = dict()

    def add_forward_config(self, target_group_arn: str, weight: int) -> None:
        self.forward_configs[target_group_arn] = weight
        return

    def is_sheddable(self, source_group_arn: str, max_shed_weight: int) -> bool:
        current_weight = self.forward_configs.get(source_group_arn)

        logger.debug(source_group_arn + ' ' + str(100 - current_weight) + ' max ' + str(max_shed_weight))
        
        if max_shed_weight == (100 - current_weight):
            return False

        return True

    def is_restorable(self, source_group_arn: str) -> bool:
        for key in self.forward_configs.keys():
            if key == source_group_arn:
                continue

            if self.forward_configs.get(key) > 0:
                return True

        return False

    def restore(self, source_group_arn: str, weight: int) -> None:
        if source_group_arn not in self.forward_configs:
            logger.debug('No target group ' + source_group_arn + ' found for rule ' + self.elb_rule_arn +
                         ' nothing to restore')

            return

        remaining_weight = weight

        for key in self.forward_configs.keys():
            if key == source_group_arn:
                continue

            weight_to_shed = remaining_weight
            current_weight = self.forward_configs.get(key)

            # restore maximum weight possible from each target.
            if (current_weight < remaining_weight):
                weight_to_shed = current_weight

            self.forward_configs[key] = current_weight - weight_to_shed

            logger.debug('Restoring ' + str(weight_to_shed) +
                         ' percent from ' + key + ' to ' + source_group_arn)

            remaining_weight -= weight_to_shed

        self.forward_configs[source_group_arn] = self.forward_configs.get(
            source_group_arn) + weight - remaining_weight
        logger.debug(
            'Restored ' + str(self.forward_configs[source_group_arn]) + ' to ' + source_group_arn)

        return

    def shed(self, source_group_arn: str, weight_to_shed: int, max_shed_weight: int) -> None:
        if source_group_arn not in self.forward_configs:
            logger.debug('No target group ' + source_group_arn + ' found for rule ' + self.elb_rule_arn +
                         ' nothing to shed')

            return

        current_source_weight = self.forward_configs.get(source_group_arn)

        if max_shed_weight == (100 - current_source_weight):
            logger.debug(
                'No more load permitted to be shed for ' + source_group_arn)

            return

        new_source_weight = current_source_weight - weight_to_shed

        if max_shed_weight < (100 - new_source_weight):
            new_source_weight = 100 - max_shed_weight
            weight_to_shed = current_source_weight - new_source_weight

            logger.debug(
                'Desired shed amount exceeds total maximum shed amount, shedding by new amount:' + str(weight_to_shed))

        # if new_source_weight < 0:
        #    # source weight cannot be < 0
        #    new_source_weight = 0

        self.forward_configs[source_group_arn] = new_source_weight

        logger.debug('Shedding ' + str(weight_to_shed) +
                     ' percent from ' + source_group_arn + '. new weight: ' + str(self.forward_configs[source_group_arn]))

        per_target_weight_to_shed = weight_to_shed

        num_forwards = len(self.forward_configs)
        remainder_weight = 0

        if num_forwards > 2:
            # if more than 2 forward configs, then split the weight evenly among the remaining 2 targets
            div_mod = divmod(weight_to_shed, (len(self.forward_configs) - 1))
            per_target_weight_to_shed = div_mod[0]
            remainder_weight = div_mod[1]

        for key in self.forward_configs.keys():
            num_forwards -= 1
            if key == source_group_arn:
                continue

            new_weight = self.forward_configs.get(
                key) + per_target_weight_to_shed

            if (num_forwards == 0):
                new_weight += remainder_weight

            logger.debug('Receiving ' + str(per_target_weight_to_shed) +
                         ' percent from ' + source_group_arn + ' on ' +
                         key + '. New load in : ' + key + ' ' + str(new_weight))

            self.forward_configs[key] = new_weight

        return

    def get_target_groups(self) -> list:
        target_groups_list = []

        for key in self.forward_configs.keys():
            target_groups_list.append(
                {'TargetGroupArn': key,
                    'Weight': self.forward_configs.get(key)}
            )

        return target_groups_list

    def save(self, elbv2_client: client):
        if not self.default_rule:
            logger.debug('Modifying rule' + self.elb_rule_arn)

            elbv2_client.modify_rule(
                RuleArn=self.elb_rule_arn,
                Actions=[
                    {
                        'Type': 'forward',
                        'ForwardConfig': {
                            'TargetGroups': self.get_target_groups()
                        }
                    }]
            )
        else:
            logger.debug('Modifying listener default rule' +
                         self.elb_listener_arn)

            elbv2_client.modify_listener(
                ListenerArn=self.elb_listener_arn,
                DefaultActions=[
                    {
                        'Type': 'forward',
                        'ForwardConfig': {
                            'TargetGroups': self.get_target_groups()
                        }
                    }]
            )

        logger.debug('Saved new forward configs: ' +
                     json.dumps(self.get_target_groups(), default=util.datetime_handler))
