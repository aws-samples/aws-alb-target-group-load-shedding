# ALB Target Group Load Shedding - Implementation Tasks

This document provides an ordered list of implementation tasks to recreate the ALB Target Group Load Shedding solution from scratch.

**Status:** This spec documents an existing implementation. All tasks below reflect the current state of the codebase.

## Phase 1: Project Setup

- [x] 1. Initialize project structure
  - [x] 1.1 Create root directory with README.md
  - [x] 1.2 Create `/cdk` directory for CDK infrastructure
  - [x] 1.3 Create `/source/lambda` directory for Lambda code
  - [x] 1.4 Create `/source/lambda/shared` directory for Lambda layer
  - [x] 1.5 Initialize CDK Python project with `cdk init app --language python`
  - [x] 1.6 Create `.gitignore` with Python and CDK exclusions

- [x] 2. Configure Python dependencies
  - [x] 2.1 Create `cdk/requirements.txt` with CDK dependencies
  - [x] 2.2 Create `cdk/Pipfile` for pipenv support
  - [x] 2.3 Create `source/lambda/shared/requirements.txt` for layer dependencies
  - [x] 2.4 Create `source/lambda/shared/setup.py` for layer packaging
  - [x] 2.5 Create `source/lambda/shared/pyproject.toml` for build configuration *(PR #28)*

## Phase 2: Lambda Layer Implementation

- [x] 3. Implement message data classes
  - [x] 3.1 Create `source/lambda/shared/elb_load_monitor/__init__.py`
  - [x] 3.2 Create `source/lambda/shared/elb_load_monitor/util.py` with datetime handler
  - [x] 3.3 Create `source/lambda/shared/elb_load_monitor/alb_alarm_messages.py`
  - [x] 3.4 Implement `CWAlarmState` enum (OK, ALARM, INSUFFICIENT_DATA)
  - [x] 3.5 Implement `ALBAlarmAction` enum (NONE, SHED, RESTORE)
  - [x] 3.6 Implement `ALBAlarmEvent` class for EventBridge events
  - [x] 3.7 Implement `ALBAlarmStatusMessage` class for SQS messages
  - [x] 3.8 Implement `to_json()` and `from_json()` serialization methods

- [x] 4. Implement ELBListenerRule class
  - [x] 4.1 Create `source/lambda/shared/elb_load_monitor/elb_listener_rule.py`
  - [x] 4.2 Implement constructor with rule ARN, listener ARN, default flag
  - [x] 4.3 Implement `add_forward_config()` method
  - [x] 4.4 Implement `is_sheddable()` method with max shed check
  - [x] 4.5 Implement `is_restorable()` method
  - [x] 4.6 Implement `shed()` method with multi-target distribution
  - [x] 4.7 Implement `restore()` method with proportional restoration
  - [x] 4.8 Implement `get_target_groups()` method
  - [x] 4.9 Implement `save()` method for default and non-default rules

- [x] 5. Implement ALBListenerRulesHandler class
  - [x] 5.1 Create `source/lambda/shared/elb_load_monitor/alb_listener_rules_handler.py`
  - [x] 5.2 Implement constructor with rule discovery from ELBv2 API
  - [x] 5.3 Implement `handle_alarm()` method for initial EventBridge events
  - [x] 5.4 Implement `handle_alarm_status_message()` method for SQS messages
  - [x] 5.5 Implement `send_sqs_notification()` method with delay configuration
  - [x] 5.6 Implement `shed()` method to iterate all rules
  - [x] 5.7 Implement `restore()` method to iterate all rules
  - [x] 5.8 Implement `is_sheddable()` and `is_restorable()` aggregation methods

## Phase 3: Lambda Function Implementation

- [x] 6. Implement ALBAlarmLambda handler
  - [x] 6.1 Create `source/lambda/alb_alarm_lambda_handler.py`
  - [x] 6.2 Initialize boto3 clients (elbv2, sqs)
  - [x] 6.3 Read environment variables for configuration
  - [x] 6.4 Parse EventBridge event and extract alarm details
  - [x] 6.5 Extract target group ARN from metric dimensions
  - [x] 6.6 Initialize ALBListenerRulesHandler with configuration
  - [x] 6.7 Call `handle_alarm()` and return response

- [x] 7. Implement ALBSQSMessageLambda handler
  - [x] 7.1 Create `source/lambda/alb_alarm_check_lambda_handler.py`
  - [x] 7.2 Initialize boto3 clients (elbv2, sqs, cloudwatch)
  - [x] 7.3 Parse SQS event and extract message body
  - [x] 7.4 Deserialize ALBAlarmStatusMessage from JSON
  - [x] 7.5 Initialize ALBListenerRulesHandler from message data
  - [x] 7.6 Call `handle_alarm_status_message()` and return response

## Phase 4: Unit Tests

- [x] 8. Create test infrastructure
  - [x] 8.1 Create `source/lambda/shared/elb_load_monitor/tests/` directory
  - [x] 8.2 Create `test_alb_listener.json` mock data
  - [x] 8.3 Create `test_cw_in_alarm.json` mock data
  - [x] 8.4 Create `test_cw_ok.json` mock data

- [x] 9. Implement ELBListenerRule tests
  - [x] 9.1 Create `test_elb_listener_rule.py`
  - [x] 9.2 Test `is_restorable()` with various weight configurations
  - [x] 9.3 Test `is_sheddable()` with max shed limits
  - [x] 9.4 Test `restore()` with single and multiple targets
  - [x] 9.5 Test `shed()` with single and multiple targets
  - [x] 9.6 Test `shed()` weight distribution with 3+ targets

- [x] 10. Implement ALBListenerRulesHandler tests
  - [x] 10.1 Create `test_alb_listener_rules_handler.py`
  - [x] 10.2 Set up mock clients and test fixtures
  - [x] 10.3 Test `handle_alarm()` with ALARM state
  - [x] 10.4 Test `handle_alarm()` with OK state
  - [x] 10.5 Test `handle_alarm()` with single shed (max limit)
  - [x] 10.6 Test `handle_alarm_status_message()` shed continuation
  - [x] 10.7 Test `handle_alarm_status_message()` restore continuation
  - [x] 10.8 Test `handle_alarm_status_message()` state transitions
  - [x] 10.9 Test `handle_alarm_status_message()` steady state detection

## Phase 5: Build Scripts

- [x] 11. Create build scripts
  - [x] 11.1 Create `source/lambda/shared/build_lambda_layer.sh`
  - [x] 11.2 Implement layer build: clean, setup.py build, zip, move to cdk/resources
  - [x] 11.3 Create `source/lambda/build_lambda_functions.sh`
  - [x] 11.4 Implement function build: zip handlers, move to cdk/resources
  - [x] 11.5 Create `cdk/resources/lambda/` directory structure
  - [x] 11.6 Create `cdk/resources/lambda_layer/` directory structure

## Phase 6: CDK Infrastructure

- [x] 12. Implement CDK stack basics
  - [x] 12.1 Create `cdk/cdk/__init__.py`
  - [x] 12.2 Create `cdk/cdk/alb_monitor_stack.py`
  - [x] 12.3 Define stack class extending cdk.Stack
  - [x] 12.4 Add context parameter for elbTargetGroupArn
  - [x] 12.5 Add CloudFormation parameters for required inputs
  - [x] 12.6 Add CloudFormation parameters for optional inputs with defaults

- [x] 13. Implement SQS queue
  - [x] 13.1 Create SQS queue resource
  - [x] 13.2 Define inline IAM policy for SQS access

- [x] 14. Implement IAM roles
  - [x] 14.1 Create ALBAlarmLambdaRole with managed policies
  - [x] 14.2 Attach CloudWatchReadOnlyAccess managed policy
  - [x] 14.3 Attach ElasticLoadBalancingFullAccess managed policy
  - [x] 14.4 Attach inline SQS policy scoped to queue ARN
  - [x] 14.5 Attach inline CloudWatch Logs policy
  - [x] 14.6 Create ALBSQSMessageLambdaRole with same permissions

- [x] 15. Implement Lambda layer
  - [x] 15.1 Define AssetCode pointing to layer zip
  - [x] 15.2 Create LayerVersion with Python 3.7/3.8 compatibility

- [x] 16. Implement ALBAlarmLambda function
  - [x] 16.1 Define AssetCode pointing to handler zip
  - [x] 16.2 Create Lambda function with handler, runtime, role
  - [x] 16.3 Configure environment variables from parameters
  - [x] 16.4 Attach Lambda layer
  - [x] 16.5 Set memory size to 128MB

- [x] 17. Implement ALBSQSMessageLambda function
  - [x] 17.1 Define AssetCode pointing to handler zip
  - [x] 17.2 Create Lambda function with handler, runtime, role
  - [x] 17.3 Attach Lambda layer
  - [x] 17.4 Add SQS event source mapping

- [x] 18. Implement CloudWatch alarm
  - [x] 18.1 Extract target group dimension from ARN
  - [x] 18.2 Create Metric with configurable namespace, name, statistic
  - [x] 18.3 Create Alarm with configurable threshold and periods
  - [x] 18.4 Set comparison operator to GREATER_THAN_THRESHOLD

- [x] 19. Implement EventBridge rule
  - [x] 19.1 Create EventBridge rule
  - [x] 19.2 Add Lambda function as target
  - [x] 19.3 Add Lambda invoke permission for EventBridge
  - [x] 19.4 Add event pattern filtering for CloudWatch alarm state changes
  - [x] 19.5 Filter for specific alarm ARN

- [x] 20. Configure CDK app
  - [x] 20.1 Create `cdk/app.py` entry point
  - [x] 20.2 Instantiate ALBMonitorStack
  - [x] 20.3 Create `cdk/cdk.json` with app command and context

## Phase 7: Documentation

- [x] 21. Create documentation
  - [x] 21.1 Create root `README.md` with architecture overview
  - [x] 21.2 Create `cdk/README.md` with deployment instructions
  - [x] 21.3 Create `source/lambda/shared/README.md` with layer build instructions
  - [x] 21.4 Document all configuration parameters
  - [x] 21.5 Document prerequisites (ALB, target groups, listener rules)

## Summary

| Phase | Tasks | Status | Notes |
|-------|-------|--------|-------|
| 1 | 1-2 | ✅ Complete | |
| 2 | 3-5 | ✅ Complete | |
| 3 | 6-7 | ✅ Complete | |
| 4 | 8-10 | ✅ Complete | 12 tests passing |
| 5 | 11 | ✅ Complete | |
| 6 | 12-20 | ✅ Complete | |
| 7 | 21 | ✅ Complete | |

**Status:** ✅ Complete (documents existing implementation)
**Completed:** 94/94 sub-tasks (100%)

## Related Specs

- **cdk-modernization** - CDK v2 migration, runtime updates, security improvements
- **testing-improvements** - pytest migration, coverage improvements
