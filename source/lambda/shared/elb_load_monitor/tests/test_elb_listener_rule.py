import unittest
from elb_load_monitor.elb_listener_rule import ELBListenerRule


class TestELBListenerRule(unittest.TestCase):

    def test_is_restorable(self) -> None:
        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 90)
        single_forward_rule.add_forward_config("secondary", 10)

        self.assertTrue(single_forward_rule.is_restorable('primary'))

        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 100)
        single_forward_rule.add_forward_config("secondary", 0)

        self.assertFalse(single_forward_rule.is_restorable('primary'))

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 95)
        two_forward_rule.add_forward_config("secondary", 5)
        two_forward_rule.add_forward_config("tertiary", 0)

        self.assertTrue(two_forward_rule.is_restorable('primary'))

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 90)
        two_forward_rule.add_forward_config("secondary", 0)
        two_forward_rule.add_forward_config("tertiary", 10)

        self.assertTrue(two_forward_rule.is_restorable('primary'))

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 100)
        two_forward_rule.add_forward_config("secondary", 0)
        two_forward_rule.add_forward_config("tertiary", 0)

        self.assertFalse(two_forward_rule.is_restorable('primary'))

    def test_is_sheddable(self) -> None:
        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 90)
        single_forward_rule.add_forward_config("secondary", 10)

        self.assertTrue(single_forward_rule.is_sheddable('primary', 100))

        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 70)
        single_forward_rule.add_forward_config("secondary", 30)

        self.assertFalse(single_forward_rule.is_sheddable('primary', 30))

        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 75)
        single_forward_rule.add_forward_config("secondary", 30)

        self.assertTrue(single_forward_rule.is_sheddable('primary', 30))

        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 100)
        single_forward_rule.add_forward_config("secondary", 0)

        self.assertTrue(single_forward_rule.is_sheddable('primary', 10))

    def test_restore(self) -> None:
        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 90)
        single_forward_rule.add_forward_config("secondary", 10)

        single_forward_rule.restore("primary", 10)
        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 100)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 0)

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 90)
        two_forward_rule.add_forward_config("secondary", 5)
        two_forward_rule.add_forward_config("tertiary", 5)

        two_forward_rule.restore("primary", 10)

        self.assertEqual(
            two_forward_rule.forward_configs.get("primary"), 100)
        self.assertEqual(
            two_forward_rule.forward_configs.get("secondary"), 0)
        self.assertEqual(
            two_forward_rule.forward_configs.get("tertiary"), 0)

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 80)
        two_forward_rule.add_forward_config("secondary", 5)
        two_forward_rule.add_forward_config("tertiary", 15)

        two_forward_rule.restore("primary", 10)

        self.assertEqual(
            two_forward_rule.forward_configs.get("primary"), 90)
        self.assertEqual(
            two_forward_rule.forward_configs.get("secondary"), 0)
        self.assertEqual(
            two_forward_rule.forward_configs.get("tertiary"), 10)

        two_forward_rule.restore("primary", 10)

        self.assertEqual(
            two_forward_rule.forward_configs.get("primary"), 100)
        self.assertEqual(
            two_forward_rule.forward_configs.get("secondary"), 0)
        self.assertEqual(
            two_forward_rule.forward_configs.get("tertiary"), 0)

    def test_shed(self) -> None:
        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 100)
        single_forward_rule.add_forward_config("secondary", 0)

        single_forward_rule.shed("primary", 10, 100)

        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 90)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 10)

        single_forward_rule.shed("primary", 10, 90)

        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 80)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 20)

        single_forward_rule.shed("primary", 10, 90)

        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 70)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 30)

        single_forward_rule.shed("primary", 10, 30)

        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 70)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 30)

        single_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        single_forward_rule.add_forward_config("primary", 100)
        single_forward_rule.add_forward_config("secondary", 0)

        single_forward_rule.shed("primary", 20, 10)

        self.assertEqual(
            single_forward_rule.forward_configs.get("primary"), 90)
        self.assertEqual(
            single_forward_rule.forward_configs.get("secondary"), 10)

        two_forward_rule = ELBListenerRule(
            "elb_rule_arn", "elb_listener_rule", False)
        two_forward_rule.add_forward_config("primary", 100)
        two_forward_rule.add_forward_config("secondary", 0)
        two_forward_rule.add_forward_config("tertiary", 0)

        two_forward_rule.shed("primary", 10, 100)

        self.assertEqual(
            two_forward_rule.forward_configs.get("primary"), 90)
        self.assertEqual(
            two_forward_rule.forward_configs.get("secondary"), 5)
        self.assertEqual(
            two_forward_rule.forward_configs.get("tertiary"), 5)

        two_forward_rule.shed("primary", 9, 100)

        self.assertEqual(
            two_forward_rule.forward_configs.get("primary"), 81)
        self.assertEqual(
            two_forward_rule.forward_configs.get("secondary"), 9)
        self.assertEqual(
            two_forward_rule.forward_configs.get("tertiary"), 10)
