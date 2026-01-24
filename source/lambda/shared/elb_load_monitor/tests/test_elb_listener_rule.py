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

    def test_shed_at_max_limit(self) -> None:
        """Test shedding when at maxElbShedPercent"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 50)
        rule.add_forward_config("secondary", 50)
        
        # Already at 50% shed (max_shed_weight=50 means PTG can only be 50)
        self.assertFalse(rule.is_sheddable('primary', 50))

    def test_shed_exceeds_max_limit(self) -> None:
        """Test shedding caps at maxElbShedPercent"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 60)
        rule.add_forward_config("secondary", 40)
        
        # Try to shed 20%, but max is 50 (PTG can only go to 50)
        rule.shed('primary', 20, 50)
        
        self.assertEqual(rule.forward_configs['primary'], 50)
        self.assertEqual(rule.forward_configs['secondary'], 50)

    def test_restore_with_zero_weight(self) -> None:
        """Test restore when STG has 0 weight"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 100)
        rule.add_forward_config("secondary", 0)
        
        # Can't restore from 0
        self.assertFalse(rule.is_restorable('primary'))

    def test_shed_with_three_target_groups(self) -> None:
        """Test shed distributes across 3+ target groups"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 100)
        rule.add_forward_config("secondary", 0)
        rule.add_forward_config("tertiary", 0)
        
        rule.shed('primary', 10, 100)
        
        # 10% should split: 5% each + remainder to last
        self.assertEqual(rule.forward_configs['primary'], 90)
        self.assertEqual(rule.forward_configs['secondary'], 5)
        self.assertEqual(rule.forward_configs['tertiary'], 5)

    def test_restore_with_remainder(self) -> None:
        """Test restore handles remainder correctly"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 90)
        rule.add_forward_config("secondary", 7)
        rule.add_forward_config("tertiary", 3)
        
        rule.restore('primary', 10)
        
        # Should restore 7 from secondary, 3 from tertiary
        self.assertEqual(rule.forward_configs['primary'], 100)
        self.assertEqual(rule.forward_configs['secondary'], 0)
        self.assertEqual(rule.forward_configs['tertiary'], 0)

    def test_weights_never_go_negative(self) -> None:
        """Test weights never go negative"""
        rule = ELBListenerRule("arn", "listener", False)
        rule.add_forward_config("primary", 10)
        rule.add_forward_config("secondary", 90)
        
        # Try to shed more than available
        rule.shed('primary', 20, 100)
        
        # Should shed all 10, not go negative
        self.assertEqual(rule.forward_configs['primary'], 0)
        self.assertEqual(rule.forward_configs['secondary'], 100)
