# ALB Target Group Load Shedding - Design Document

## 1. System Overview

### 1.1 Purpose

The ALB Target Group Load Shedding (ALB TGLS) solution provides automated traffic management for Application Load Balancers during high-load scenarios. When a CloudWatch alarm breaches its threshold, the system incrementally shifts traffic from a Primary Target Group (PTG) to a Shedding Target Group (STG), allowing the primary infrastructure to recover. Once the alarm clears, traffic is gradually restored.

### 1.2 Design Goals

- **Gradual Transitions**: Avoid abrupt traffic shifts that could cause cascading failures
- **Self-Healing**: Automatically restore normal operation when conditions improve
- **Configurable**: Allow operators to tune shedding/restore rates and thresholds
- **Stateless**: Lambda functions operate statelessly using message-based state transfer
- **Observable**: Comprehensive logging for troubleshooting and auditing

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   CloudWatch    │────▶│   EventBridge   │────▶│  ALBAlarmLambda     │
│     Alarm       │     │      Rule       │     │  (Initial Handler)  │
└─────────────────┘     └─────────────────┘     └──────────┬──────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  ALB Listener   │◀────│  ALBSQSMessage  │◀────│     SQS Queue       │
│     Rules       │     │     Lambda      │     │  (Delayed Actions)  │
└─────────────────┘     └─────────────────┘     └─────────────────────┘
```

### 2.2 Component Interactions

1. **CloudWatch Alarm** monitors `RequestCountPerTarget` metric
2. **EventBridge Rule** captures alarm state changes and invokes Lambda
3. **ALBAlarmLambda** performs initial shed/restore and queues follow-up
4. **SQS Queue** holds delayed messages for incremental actions
5. **ALBSQSMessageLambda** processes delayed messages and continues cycle
6. **ALB Listener Rules** are modified to adjust traffic weights

### 2.3 AWS Services Used

| Service | Purpose |
|---------|---------|
| CloudWatch | Metric monitoring and alarming |
| EventBridge | Event routing from CloudWatch to Lambda |
| Lambda | Serverless compute for shedding logic |
| SQS | Message queue for delayed action scheduling |
| Elastic Load Balancing | Traffic distribution via weighted target groups |
| IAM | Access control and permissions |
| CloudWatch Logs | Logging and observability |

## 3. Component Design

### 3.1 Lambda Functions

#### 3.1.1 ALBAlarmLambda (alb_alarm_lambda_handler.py)

**Trigger**: EventBridge rule on CloudWatch alarm state change

**Responsibilities**:
- Parse CloudWatch alarm event
- Extract target group ARN from metric dimensions
- Initialize ALBListenerRulesHandler with configuration
- Execute initial shed (on ALARM) or prepare restore (on OK)
- Queue follow-up message to SQS

**Environment Variables**:
```
ELB_ARN              - Load balancer ARN
ELB_LISTENER_ARN     - Listener ARN to modify
SQS_QUEUE_URL        - Queue for delayed messages
ELB_SHED_PERCENT     - Percentage to shed per interval
MAX_ELB_SHED_PERCENT - Maximum total shed percentage
ELB_RESTORE_PERCENT  - Percentage to restore per interval
SHED_MESG_DELAY_SEC  - Delay between shed actions
RESTORE_MESG_DELAY_SEC - Delay between restore actions
```

#### 3.1.2 ALBSQSMessageLambda (alb_alarm_check_lambda_handler.py)

**Trigger**: SQS event source

**Responsibilities**:
- Parse SQS message containing ALBAlarmStatusMessage
- Query current CloudWatch alarm state
- Execute shed or restore based on current state
- Queue follow-up message if more action needed
- Stop when steady state reached

### 3.2 Lambda Layer (elb_load_monitor)

#### 3.2.1 ALBListenerRulesHandler

**Purpose**: Orchestrates listener rule discovery and modification

**Key Methods**:
```python
handle_alarm(elbv2_client, sqs_client, sqs_queue_url, alb_alarm_event)
    # Handles initial alarm event from EventBridge
    # Returns: ALBAlarmAction (SHED, RESTORE, or NONE)

handle_alarm_status_message(cw_client, elbv2_client, sqs_client, alb_alarm_status_message)
    # Handles follow-up message from SQS
    # Re-evaluates alarm state before action
    # Returns: ALBAlarmAction

shed(elbv2_client, source_group_arn, weight, max_shed_weight)
    # Sheds specified weight from source target group

restore(elbv2_client, source_group_arn, weight)
    # Restores specified weight to source target group

is_sheddable(source_group_arn, max_shed_weight)
    # Returns True if more shedding is possible

is_restorable(source_group_arn)
    # Returns True if traffic can be restored
```

#### 3.2.2 ELBListenerRule

**Purpose**: Represents a single listener rule with forward configuration

**Key Methods**:
```python
add_forward_config(target_group_arn, weight)
    # Adds target group to rule's forward configuration

shed(source_group_arn, weight_to_shed, max_shed_weight)
    # Reduces weight on source, distributes to other targets

restore(source_group_arn, weight)
    # Increases weight on source, reduces from other targets

save(elbv2_client)
    # Persists weight changes to ALB via API

get_target_groups()
    # Returns list of target group configurations
```

#### 3.2.3 Message Classes

**CWAlarmState** (Enum):
- OK
- ALARM
- INSUFFICIENT_DATA

**ALBAlarmAction** (Enum):
- NONE - No action taken
- SHED - Traffic being shed from PTG
- RESTORE - Traffic being restored to PTG

**ALBAlarmEvent**: Represents initial CloudWatch alarm event
**ALBAlarmStatusMessage**: Represents SQS message for follow-up actions

## 4. Algorithms

### 4.1 Shedding Algorithm

```
Input: source_group_arn, weight_to_shed, max_shed_weight
Current State: forward_configs[target_group_arn] = weight

1. Get current_source_weight from forward_configs[source_group_arn]

2. Check if max shed reached:
   if max_shed_weight == (100 - current_source_weight):
       return  # Cannot shed more

3. Calculate new_source_weight:
   new_source_weight = current_source_weight - weight_to_shed

4. Enforce max shed limit:
   if max_shed_weight < (100 - new_source_weight):
       new_source_weight = 100 - max_shed_weight
       weight_to_shed = current_source_weight - new_source_weight

5. Update source weight:
   forward_configs[source_group_arn] = new_source_weight

6. Distribute shed weight to other targets:
   if num_targets > 2:
       per_target_weight = weight_to_shed / (num_targets - 1)
       remainder = weight_to_shed % (num_targets - 1)
   else:
       per_target_weight = weight_to_shed
       remainder = 0

7. For each non-source target:
       forward_configs[target] += per_target_weight
       if last_target:
           forward_configs[target] += remainder
```

### 4.2 Restore Algorithm

```
Input: source_group_arn, weight_to_restore
Current State: forward_configs[target_group_arn] = weight

1. remaining_weight = weight_to_restore

2. For each non-source target:
       current_weight = forward_configs[target]
       weight_to_take = min(remaining_weight, current_weight)
       forward_configs[target] -= weight_to_take
       remaining_weight -= weight_to_take

3. Update source weight:
   forward_configs[source_group_arn] += (weight_to_restore - remaining_weight)
```

### 4.3 State Machine

```
                    ┌──────────────────┐
                    │   STEADY STATE   │
                    │  (PTG=100%, OK)  │
                    └────────┬─────────┘
                             │ Alarm → ALARM
                             ▼
                    ┌──────────────────┐
              ┌────▶│    SHEDDING      │◀────┐
              │     │  (PTG weight ↓)  │     │
              │     └────────┬─────────┘     │
              │              │               │
    Still ALARM,       Alarm → OK      Still ALARM,
    can shed more                      max not reached
              │              │               │
              └──────────────┼───────────────┘
                             ▼
                    ┌──────────────────┐
              ┌────▶│   RESTORING      │◀────┐
              │     │  (PTG weight ↑)  │     │
              │     └────────┬─────────┘     │
              │              │               │
         Still OK,     PTG = 100%      Alarm → ALARM
         can restore                   (switch to SHED)
              │              │               │
              └──────────────┼───────────────┘
                             ▼
                    ┌──────────────────┐
                    │   STEADY STATE   │
                    │  (PTG=100%, OK)  │
                    └──────────────────┘
```

## 5. Data Flow

### 5.1 EventBridge Event Format

```json
{
  "id": "event-id",
  "detail-type": "CloudWatch Alarm State Change",
  "source": "aws.cloudwatch",
  "account": "123456789012",
  "region": "us-east-1",
  "resources": ["arn:aws:cloudwatch:...alarm:ALBTargetGroupAlarm"],
  "detail": {
    "alarmName": "ALBTargetGroupAlarm",
    "state": {
      "value": "ALARM"
    },
    "configuration": {
      "metrics": [{
        "metricStat": {
          "metric": {
            "dimensions": {
              "TargetGroup": "targetgroup/MyTG/abc123"
            }
          }
        }
      }]
    }
  }
}
```

### 5.2 SQS Message Format (ALBAlarmStatusMessage)

```json
{
  "albAlarmAction": "SHED",
  "alarmArn": "arn:aws:cloudwatch:...:alarm:ALBTargetGroupAlarm",
  "alarmName": "ALBTargetGroupAlarm",
  "elbListenerArn": "arn:aws:elasticloadbalancing:...:listener/...",
  "elbShedPercent": 5,
  "maxElbShedPercent": 100,
  "elbRestorePercent": 5,
  "loadBalancerArn": "arn:aws:elasticloadbalancing:...:loadbalancer/...",
  "sqsQueueURL": "https://sqs.region.amazonaws.com/account/queue",
  "shedMesgDelaySec": 60,
  "restoreMesgDelaySec": 120,
  "targetGroupArn": "arn:aws:elasticloadbalancing:...:targetgroup/..."
}
```

## 6. Infrastructure Design

### 6.1 CDK Stack Structure

```
ALBMonitorStack
├── SQS Queue (alb_target_group_monitor_queue)
├── IAM Role (ALBAlarmLambdaRole)
│   ├── CloudWatchReadOnlyAccess (managed)
│   ├── ElasticLoadBalancingFullAccess (managed)
│   ├── SQS permissions (inline)
│   └── CloudWatch Logs permissions (inline)
├── Lambda Layer (ALBMonitorLayer)
├── Lambda Function (ALBAlarmLambda)
│   ├── EventBridge trigger
│   └── Environment variables
├── IAM Role (ALBSQSMessageLambdaRole)
├── Lambda Function (ALBSQSMessageLambda)
│   └── SQS event source
├── CloudWatch Alarm (ALBTargetGroupAlarm)
└── EventBridge Rule (ALBTargetGroupAlarmEventRule)
    └── Lambda target
```

### 6.2 IAM Permissions

**Lambda Execution Roles require**:
- `cloudwatch:DescribeAlarms` - Query alarm state
- `elasticloadbalancing:DescribeRules` - List listener rules
- `elasticloadbalancing:ModifyRule` - Update rule weights
- `elasticloadbalancing:ModifyListener` - Update default rule
- `sqs:SendMessage` - Queue follow-up messages
- `sqs:ReceiveMessage` - Process queued messages
- `sqs:DeleteMessage` - Remove processed messages
- `logs:CreateLogGroup/Stream/PutLogEvents` - Logging

## 7. Error Handling

### 7.1 Error Scenarios

| Scenario | Handling |
|----------|----------|
| Listener not found | Log error, return without action |
| Alarm not found | Log error, return NONE action |
| No SQS message | Log warning, return |
| Unsupported event type | Return 403 status |
| Target group not in rule | Skip rule, continue with others |

### 7.2 Retry Behavior

- SQS messages remain in queue on Lambda failure
- Default SQS visibility timeout applies
- No explicit dead-letter queue configured

## 8. Testing Strategy

### 8.1 Test Coverage Summary

| Category | Status | Details |
|----------|--------|---------|
| Test Files | 2 | `test_alb_listener_rules_handler.py`, `test_elb_listener_rule.py` |
| Test Methods | 12 | 8 handler tests, 4 rule tests |
| Framework | unittest | `nose` in setup.py (deprecated) |

### 8.2 What's Tested ✅

**test_alb_listener_rules_handler.py** (8 tests):
- `test_handle_alarm` - Initial ALARM state handling
- `test_handle_alarm_single_shed` - Max shed limit enforcement
- `test_handle_alarm_other_states` - OK state handling
- `test_handle_alarm_status_message_shed` - Follow-up shed actions
- `test_handle_alarm_status_message_shed_previous_restore` - State transitions
- `test_handle_alarm_status_message_restore` - Follow-up restore actions
- `test_handle_alarm_status_message_restore_previous_shed` - State transitions
- `test_handle_alarm_status_message_restore_no_remaining_restore` - Steady state

**test_elb_listener_rule.py** (4 tests):
- `test_is_restorable` - Restore eligibility logic
- `test_is_sheddable` - Shed eligibility logic
- `test_restore` - Restore weight calculations
- `test_shed` - Shed weight calculations

### 8.3 Test Gaps ❌

| Missing Coverage | File/Component | Priority |
|------------------|----------------|----------|
| Lambda handlers | `alb_alarm_lambda_handler.py` | High |
| Lambda handlers | `alb_alarm_check_lambda_handler.py` | High |
| CDK stack | `alb_monitor_stack.py` | Medium |
| Message serialization | `ALBAlarmStatusMessage.to_json/from_json` | Medium |
| Error handling paths | Exception scenarios | Medium |
| Integration tests | End-to-end flow | Low |

### 8.4 Test Data

- `test_alb_listener.json` - Mock ALB listener rules response
- `test_cw_in_alarm.json` - Mock CloudWatch alarm in ALARM state
- `test_cw_ok.json` - Mock CloudWatch alarm in OK state

### 8.5 Testing Improvements Needed

1. **Migrate to pytest** - Replace deprecated `nose` framework
2. **Add Lambda handler tests** - Mock boto3 clients and test event parsing
3. **Add CDK snapshot tests** - Verify CloudFormation output
4. **Add message serialization tests** - Verify JSON round-trip
5. **Add error path tests** - Test exception handling
6. **Add integration tests** - LocalStack or moto-based tests

## 9. Build and Deployment

### 9.1 Build Process

```bash
# Build Lambda layer
cd source/lambda/shared
./build_lambda_layer.sh
# Output: cdk/resources/lambda_layer/elb_load_monitor.zip

# Build Lambda functions
cd source/lambda
./build_lambda_functions.sh
# Output: cdk/resources/lambda/alb_alarm_lambda_handler.zip
# Output: cdk/resources/lambda/alb_alarm_check_lambda_handler.zip
```

### 9.2 CDK Deployment

```bash
cd cdk

# Bootstrap (first time)
cdk bootstrap -c elbTargetGroupArn="<TARGET_GROUP_ARN>"

# Synthesize
cdk synth -c elbTargetGroupArn="<TARGET_GROUP_ARN>"

# Deploy
cdk deploy ALBMonitorStack \
  -c elbTargetGroupArn="<TARGET_GROUP_ARN>" \
  --parameters elbArn="<ELB_ARN>" \
  --parameters elbListenerArn="<LISTENER_ARN>"
```

## 10. Constraints and Limitations

### 10.1 Design Constraints

1. **Single Alarm per Deployment**: Each stack monitors one CloudWatch alarm
2. **Single Listener**: Each stack manages one ALB listener
3. **Weight Granularity**: ALB weights are integers 0-100
4. **Minimum Delay**: SQS delay minimum is 60 seconds
5. **Maximum Delay**: SQS delay maximum is 300 seconds (5 minutes)

### 10.2 Known Limitations

1. **No VPC Configuration**: Lambda functions not placed in VPC by default
2. **No Dead-Letter Queue**: Failed messages not captured separately
3. **No Metrics**: Custom CloudWatch metrics not emitted
4. **Python 3.8**: Runtime version may need updating
5. **CDK v1**: Uses older CDK version (aws-cdk.core)

### 10.3 Assumptions

1. ALB and target groups already exist
2. Listener rules pre-configured with weighted target groups
3. PTG starts with 100% weight, STG with 0%
4. STG has capacity to handle shed traffic
5. Network connectivity between Lambda and AWS APIs

## 11. Technical Debt & Modernization Required

**Review Date:** January 2025

### 11.1 Critical Issues (Must Fix)

| Issue | Current State | Required State | Impact |
|-------|---------------|----------------|--------|
| AWS CDK v1 EOL | `aws-cdk.aws-*>=1.107` | `aws-cdk-lib>=2.0.0` | Security vulnerabilities, no support |
| Lambda Runtime | Python 3.8 | Python 3.12+ | Deprecated runtime, no patches |
| boto3/botocore | 1.16.29/1.19.29 (Dec 2020) | 1.34.0+ | Missing 4 years of updates |
| constructs | 3.3.75 | 10.0.0+ | CDK v1 dependency |

### 11.2 High Priority Issues

| Issue | Location | Recommendation |
|-------|----------|----------------|
| Deprecated feature flags | `cdk/cdk.json` | Remove all v1 flags (active by default in v2) |
| Overly permissive IAM | `alb_monitor_stack.py` | Replace `ElasticLoadBalancingFullAccess` with specific permissions |
| No Dead Letter Queue | SQS Queue | Add DLQ with 14-day retention |
| No Lambda timeout | Lambda functions | Add 30-second timeout |

### 11.3 Medium Priority Issues

| Issue | Location | Recommendation |
|-------|----------|----------------|
| Deprecated test framework | `setup.py` | Replace `nose` with `pytest` |
| Missing type hints | All Python files | Add type annotations |
| Hardcoded function names | `alb_monitor_stack.py` | Use stack-prefixed names |
| Outdated packages | `requirements.txt` | Remove unused CDK v1 deps (jsii, six) |

### 11.4 Low Priority Issues

| Issue | Location | Recommendation |
|-------|----------|----------------|
| `logger.warn` deprecated | `alb_listener_rules_handler.py` | Use `logger.warning` |
| String concatenation in logs | Multiple files | Use parameterized logging |
| Unused import | `elb_listener_rule.py` | Remove `from re import S` |
| Empty `__init__.py` | `elb_load_monitor/__init__.py` | Add `__all__` exports |

### 11.5 Migration Effort Estimate

| Phase | Effort | Risk |
|-------|--------|------|
| CDK v2 Migration | 4-8 hours | Medium |
| Runtime Update | 1-2 hours | Low |
| Dependency Updates | 2-4 hours | Medium |
| Security Improvements | 2-4 hours | Low |
| Code Quality | 4-6 hours | Low |
| **Total** | **13-24 hours** | |

## 12. Future Considerations

1. **Multi-Alarm Support**: Monitor multiple metrics/alarms
2. **Custom Metrics**: Emit operational metrics to CloudWatch
3. **SNS Notifications**: Alert operators on state changes
4. **VPC Support**: Deploy Lambda in VPC with endpoints
5. **Step Functions**: Replace SQS-based state machine
6. **Configurable Strategies**: Different shedding algorithms
7. **X-Ray Tracing**: Add distributed tracing
8. **Cost Allocation Tags**: Add resource tagging
