# ALB Target Group Load Shedding - Requirements

## Overview

This document captures the functional and non-functional requirements for the ALB Target Group Load Shedding (ALB TGLS) solution. The solution automatically manages traffic distribution between Application Load Balancer target groups based on CloudWatch alarm states, enabling graceful degradation during high-load scenarios.

## Functional Requirements

### 1. CloudWatch Alarm Integration

#### 1.1 Alarm State Detection
- **As a** system operator
- **I want** the system to detect CloudWatch alarm state changes
- **So that** load shedding can be triggered automatically when thresholds are breached

**Acceptance Criteria:**
- System receives CloudWatch alarm state change events via EventBridge
- System handles ALARM, OK, and INSUFFICIENT_DATA states
- Alarm configuration supports customizable namespace, metric name, statistic, threshold, and evaluation periods
- Default metric is `RequestCountPerTarget` in `AWS/ApplicationELB` namespace

#### 1.2 Configurable Alarm Parameters
- **As a** system operator
- **I want** to configure alarm thresholds and evaluation periods
- **So that** I can tune the sensitivity of load shedding triggers

**Acceptance Criteria:**
- Configurable CloudWatch namespace (default: `AWS/ApplicationELB`)
- Configurable metric name (default: `RequestCountPerTarget`)
- Configurable statistic function (default: `sum`)
- Configurable threshold value (default: 500)
- Configurable evaluation periods (default: 3)
- Alarm evaluation period fixed at 60 seconds

### 2. Load Shedding Operations

#### 2.1 Incremental Traffic Shedding
- **As a** system operator
- **I want** traffic to be shed incrementally from the Primary Target Group (PTG) to the Shedding Target Group (STG)
- **So that** the system can gradually reduce load without abrupt traffic shifts

**Acceptance Criteria:**
- Traffic is shed in configurable percentage increments (default: 5%)
- Shed percentage is configurable between 0-100%
- Maximum shed percentage is configurable (default: 100%)
- Shedding stops when maximum shed percentage is reached
- ALB listener rule weights are updated to reflect new traffic distribution

#### 2.2 Incremental Traffic Restoration
- **As a** system operator
- **I want** traffic to be restored incrementally from STG back to PTG when the alarm clears
- **So that** the system can gradually return to normal operation without overwhelming the PTG

**Acceptance Criteria:**
- Traffic is restored in configurable percentage increments (default: 5%)
- Restore percentage is configurable between 0-100%
- Restoration continues until PTG has 100% traffic weight
- Restoration stops when no more traffic remains on STG

#### 2.3 Multi-Target Group Support
- **As a** system operator
- **I want** the system to handle multiple target groups in a listener rule
- **So that** traffic can be distributed across more than two target groups

**Acceptance Criteria:**
- System supports 2+ target groups per listener rule
- When shedding with 3+ target groups, shed weight is distributed evenly among non-primary groups
- Remainder weight from uneven division is assigned to the last target group
- Restoration pulls weight from all non-primary target groups proportionally

### 3. Delayed Action Processing

#### 3.1 SQS-Based Delay Mechanism
- **As a** system operator
- **I want** subsequent shedding/restore actions to be delayed
- **So that** the system has time to stabilize between adjustments

**Acceptance Criteria:**
- Shed actions are delayed by configurable interval (default: 60 seconds, range: 60-300)
- Restore actions are delayed by configurable interval (default: 120 seconds, range: 60-300)
- Delays are implemented using SQS message visibility timeout
- Messages contain full state for stateless Lambda processing

#### 3.2 State Re-evaluation
- **As a** system operator
- **I want** the system to re-evaluate alarm state before each action
- **So that** actions are only taken when still appropriate

**Acceptance Criteria:**
- System queries current CloudWatch alarm state before each action
- If alarm state changed (e.g., ALARM → OK), action type switches accordingly
- INSUFFICIENT_DATA state causes re-queue with previous action type
- No action taken when system reaches steady state (100% PTG, alarm OK)

### 4. ALB Listener Rule Management

#### 4.1 Rule Discovery
- **As a** system operator
- **I want** the system to automatically discover listener rules
- **So that** I don't need to manually configure each rule

**Acceptance Criteria:**
- System retrieves all rules for the specified listener ARN
- System identifies forward-type actions with target group configurations
- System handles both default and non-default rules
- System skips redirect and fixed-response actions

#### 4.2 Rule Modification
- **As a** system operator
- **I want** the system to update listener rule weights
- **So that** traffic distribution changes take effect

**Acceptance Criteria:**
- Non-default rules are modified via `modify_rule` API
- Default rules are modified via `modify_listener` API
- All rules with the target group are updated consistently
- Weight changes are persisted to ALB configuration

### 5. Event-Driven Architecture

#### 5.1 EventBridge Integration
- **As a** system operator
- **I want** CloudWatch alarm state changes to trigger Lambda functions via EventBridge
- **So that** the system responds automatically to alarm events

**Acceptance Criteria:**
- EventBridge rule filters for `CloudWatch Alarm State Change` events
- Rule filters for specific alarm ARN
- Lambda function is invoked with full event payload
- Event contains alarm name, state, and metric configuration

#### 5.2 SQS Event Source
- **As a** system operator
- **I want** delayed messages to trigger Lambda processing
- **So that** incremental actions continue automatically

**Acceptance Criteria:**
- Lambda function configured with SQS event source
- Messages processed one at a time
- Failed messages remain in queue for retry
- Message body contains full action context

## Non-Functional Requirements

### 6. Performance

#### 6.1 Lambda Execution
- Lambda functions configured with 128MB memory
- Python 3.8 runtime
- Shared code deployed as Lambda layer

#### 6.2 Response Time
- Initial alarm response within seconds of EventBridge delivery
- Subsequent actions delayed by configured intervals

### 7. Security

#### 7.1 IAM Permissions
- Lambda execution roles follow least-privilege principle
- CloudWatch read-only access for alarm state queries
- Elastic Load Balancing full access for rule modifications
- SQS permissions scoped to specific queue ARN
- CloudWatch Logs permissions for logging

#### 7.2 Resource Isolation
- SQS queue created per deployment
- IAM policies reference specific resource ARNs

### 8. Reliability

#### 8.1 Error Handling
- System logs errors for missing alarms or listeners
- System handles boto3 exceptions gracefully
- Unsupported event types return 403 status

#### 8.2 Idempotency
- Actions are idempotent - repeated execution produces same result
- Weight calculations based on current state, not assumed state

### 9. Observability

#### 9.1 Logging
- All Lambda functions log to CloudWatch Logs
- Event payloads logged at INFO level
- Debug logging available for detailed troubleshooting
- JSON serialization handles datetime objects

### 10. Deployment

#### 10.1 Infrastructure as Code
- AWS CDK (Python) for infrastructure definition
- CloudFormation parameters for runtime configuration
- Context parameters for synthesis-time configuration

#### 10.2 Build Process
- Shell scripts for Lambda function packaging
- Separate build for Lambda layer
- Built artifacts stored in `cdk/resources/` directory

## Configuration Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| elbArn | String | Required | - | ARN of the Application Load Balancer |
| elbTargetGroupArn | String | Required | - | ARN of the Primary Target Group |
| elbListenerArn | String | Required | - | ARN of the ALB Listener |
| elbShedPercent | Number | 5 | 0-100 | Percentage to shed per interval |
| elbRestorePercent | Number | 5 | 0-100 | Percentage to restore per interval |
| maxElbShedPercent | Number | 100 | 0-100 | Maximum total percentage to shed |
| shedMesgDelaySec | Number | 60 | 60-300 | Delay between shed actions (seconds) |
| restoreMesgDelaySec | Number | 120 | 60-300 | Delay between restore actions (seconds) |
| cwAlarmNamespace | String | AWS/ApplicationELB | - | CloudWatch metric namespace |
| cwAlarmMetricName | String | RequestCountPerTarget | - | CloudWatch metric name |
| cwAlarmMetricStat | String | sum | - | Metric aggregation statistic |
| cwAlarmThreshold | Number | 500 | - | Alarm threshold value |
| cwAlarmPeriods | Number | 3 | - | Number of evaluation periods |

## Prerequisites

1. Application Load Balancer with appropriate Target Groups deployed
2. ALB listener weighted rules configured with:
   - 100% weight to Primary Target Group
   - 0% weight to Shedding Target Group
3. AWS CDK installed and configured
4. Python 3.8+ environment
