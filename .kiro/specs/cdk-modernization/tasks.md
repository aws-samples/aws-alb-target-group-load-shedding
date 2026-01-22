# CDK Modernization - Implementation Tasks

## Phase 1: CDK v2 Migration

- [ ] 1. Update CDK dependencies
  - [ ] 1.1 Update `cdk/requirements.txt` to use `aws-cdk-lib>=2.170.0`
  - [ ] 1.2 Update `cdk/requirements.txt` to use `constructs>=10.0.0`
  - [ ] 1.3 Remove individual `aws-cdk.aws-*` packages
  - [ ] 1.4 Remove `jsii` and `six` dependencies
  - [ ] 1.5 Update `cdk/Pipfile` with new dependencies
  - [ ] 1.6 Regenerate `cdk/Pipfile.lock`

- [ ] 2. Update CDK stack imports
  - [ ] 2.1 Replace `from aws_cdk import core as cdk` with `from aws_cdk import Stack, Duration, CfnParameter`
  - [ ] 2.2 Update all `aws_cdk.aws_*` imports to `from aws_cdk import aws_* as *`
  - [ ] 2.3 Replace `cdk.Construct` with `Construct` from `constructs`
  - [ ] 2.4 Replace `cdk.Stack` with `Stack`
  - [ ] 2.5 Replace `cdk.Duration` with `Duration`
  - [ ] 2.6 Replace `cdk.CfnParameter` with `CfnParameter`

- [ ] 3. Update CDK app
  - [ ] 3.1 Update `cdk/app.py` imports
  - [ ] 3.2 Replace `core.App()` with `App()` from `aws_cdk`

- [ ] 4. Remove deprecated feature flags
  - [ ] 4.1 Remove `@aws-cdk/core:enableStackNameDuplicates` from `cdk.json`
  - [ ] 4.2 Remove `aws-cdk:enableDiffNoFail` from `cdk.json`
  - [ ] 4.3 Remove `@aws-cdk/core:stackRelativeExports` from `cdk.json`

## Phase 2: Lambda Runtime Update

- [ ] 5. Update Lambda runtime
  - [ ] 5.1 Change `_lambda.Runtime.PYTHON_3_8` to `_lambda.Runtime.PYTHON_3_12`
  - [ ] 5.2 Update Lambda layer compatible runtimes to Python 3.11/3.12
  - [ ] 5.3 Verify Python 3.12 compatibility in Lambda handler code
  - [ ] 5.4 Verify Python 3.12 compatibility in Lambda layer code

## Phase 3: Dependency Updates

- [ ] 6. Update boto3/botocore
  - [ ] 6.1 Update `source/lambda/shared/requirements.txt` boto3 to 1.34.0+
  - [ ] 6.2 Update `source/lambda/shared/requirements.txt` botocore to 1.34.0+
  - [ ] 6.3 Update `source/lambda/shared/Pipfile` with new versions
  - [ ] 6.4 Regenerate `source/lambda/shared/Pipfile.lock`
  - [ ] 6.5 Verify all AWS API calls work with updated SDK

## Phase 4: Security Improvements

- [ ] 7. Implement IAM least privilege
  - [ ] 7.1 Replace `ElasticLoadBalancingFullAccess` managed policy
  - [ ] 7.2 Add inline policy with specific ELB permissions
  - [ ] 7.3 Scope permissions to specific resources where possible
  - [ ] 7.4 Document required permissions in README

- [ ] 8. Add Dead Letter Queue
  - [ ] 8.1 Create DLQ resource with 14-day retention
  - [ ] 8.2 Configure main queue with DLQ redrive policy
  - [ ] 8.3 Set maxReceiveCount to 3
  - [ ] 8.4 Add CloudWatch alarm for DLQ messages (optional)

- [ ] 9. Add Lambda timeouts
  - [ ] 9.1 Add 30-second timeout to ALBAlarmLambda
  - [ ] 9.2 Add 30-second timeout to ALBSQSMessageLambda

## Phase 5: Code Quality

- [ ] 10. Fix deprecation warnings
  - [ ] 10.1 Replace `logger.warn` with `logger.warning` in `alb_listener_rules_handler.py`
  - [ ] 10.2 Use parameterized logging instead of string concatenation
  - [ ] 10.3 Remove unused `from re import S` in `elb_listener_rule.py`
  - [ ] 10.4 Add `__all__` exports to `elb_load_monitor/__init__.py`

- [ ] 11. Add type hints (optional)
  - [ ] 11.1 Add type hints to `alb_alarm_messages.py`
  - [ ] 11.2 Add type hints to `elb_listener_rule.py`
  - [ ] 11.3 Add type hints to `alb_listener_rules_handler.py`
  - [ ] 11.4 Add type hints to Lambda handlers

## Phase 6: Validation

- [ ] 12. Validate migration
  - [ ] 12.1 Run existing unit tests
  - [ ] 12.2 Run `cdk synth` to validate CloudFormation
  - [ ] 12.3 Review generated CloudFormation template
  - [ ] 12.4 Compare CloudFormation diff with previous version
  - [ ] 12.5 Deploy to test environment
  - [ ] 12.6 Trigger alarm and verify shedding behavior
  - [ ] 12.7 Clear alarm and verify restore behavior
  - [ ] 12.8 Verify DLQ captures failed messages

## Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1 | 1-4 | 4-8h | ⬜ Not Started |
| 2 | 5 | 1-2h | ⬜ Not Started |
| 3 | 6 | 2-4h | ⬜ Not Started |
| 4 | 7-9 | 2-4h | ⬜ Not Started |
| 5 | 10-11 | 4-6h | ⬜ Not Started |
| 6 | 12 | 2-4h | ⬜ Not Started |

**Total Estimated Effort:** 13-24 hours
**Total Sub-tasks:** 52
