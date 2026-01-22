---
inclusion: always
---

# ALB Target Group Load Shedding Project

Automated load shedding solution for Application Load Balancers that prevents overload by incrementally redistributing traffic between Primary and Shedding Target Groups based on CloudWatch metrics.

## Core Concept

**Load Shedding:** Sacrifice enough traffic to maintain partial availability during overload. Critical when cold start times reduce autoscaling effectiveness.

**Why ALB vs DNS:** ALB weighted target groups respond immediately to weight changes, unlike DNS which requires TTL expiration.

## Architecture Flow

1. **CloudWatch Alarm** breaches (e.g., RequestCountPerTarget > threshold) → **EventBridge** triggers
2. **ALBAlarmLambda** evaluates alarm state:
   - ALARM → Shed X% from PTG to STG
   - OK → Restore X% from STG to PTG
   - Sends SQS message with delay
3. **SQS** delivers delayed message → **ALBSQSMessageLambda** re-evaluates
4. **Loop continues** until 100% restored to PTG or max shed limit reached

## Project Structure

```
/cdk/                                    # CDK infrastructure (Python)
  alb_monitor_stack.py                   # Main stack: Lambda, SQS, EventBridge, CloudWatch
  app.py                                 # CDK entry point
  resources/                             # Built artifacts
    lambda/                              # Zipped Lambda functions
    lambda_layer/                        # Zipped shared layer

/source/lambda/                          # Lambda source code
  alb_alarm_lambda_handler.py            # Handles EventBridge alarm events
  alb_alarm_check_lambda_handler.py      # Processes SQS messages
  build_lambda_functions.sh              # Builds Lambda zips
  
  shared/elb_load_monitor/               # Shared Lambda layer
    alb_listener_rules_handler.py        # Core shedding/restore logic
    elb_listener_rule.py                 # Manages ALB listener rule weights
    alb_alarm_messages.py                # Event/message data models
    util.py                              # Datetime helpers
    build_lambda_layer.sh                # Builds layer zip
    tests/                               # Unit tests
```

## Key Components

**Lambda Functions:**
- `ALBAlarmLambda` - Triggered by EventBridge, initiates shed/restore
- `ALBSQSMessageLambda` - Triggered by SQS, continues incremental adjustments

**Core Logic (`elb_load_monitor` layer):**
- `ALBListenerRulesHandler` - Orchestrates shed/restore actions
- `ELBListenerRule` - Calculates and applies weight changes
- `ALBAlarmStatusMessage` - Carries state between Lambda invocations

**Shedding Algorithm:**
- Decreases PTG weight by X%, distributes proportionally to other target groups
- Respects `maxElbShedPercent` limit
- Handles multiple target groups (splits evenly with remainder handling)

**Restoring Algorithm:**
- Increases PTG weight by X%, takes from other target groups proportionally
- Stops when all other target groups reach 0 weight

## Configuration Parameters

**Required (CDK deploy):**
- `elbArn` - ALB ARN
- `elbListenerArn` - Listener ARN
- `elbTargetGroupArn` - Primary Target Group ARN (context param)

**Optional (defaults shown):**
- `elbShedPercent=5` - % to shed per interval
- `elbRestorePercent=5` - % to restore per interval
- `maxElbShedPercent=100` - Max total shed allowed
- `shedMesgDelaySec=60` - Delay between shed actions
- `restoreMesgDelaySec=120` - Delay between restore actions
- `cwAlarmThreshold=500` - Alarm threshold
- `cwAlarmMetricName=RequestCountPerTarget` - Metric to monitor
- `cwAlarmMetricStat=sum` - Aggregation function
- `cwAlarmPeriods=3` - Evaluation periods

## Common Use Cases

**Metrics for Different Scenarios:**
- `RequestCountPerTarget` - Known max request capacity
- `ActiveConnectionCount` - TCP connection limits
- `TargetResponseTime` - SLA requirements
- `HealthyHostCount` - Grace period for autoscaling
- `HTTPCode_Target_5XX_Count` - Error rate thresholds

**Shedding Target Group Strategies:**
1. **Standby EC2 fleet** - Best-effort serving or custom error pages
2. **Lambda targets** - Cost-effective custom responses
3. **Empty STG** - Drop traffic (ALB returns 503)

## Build & Deploy

```bash
# Build Lambda artifacts
cd source/lambda
./build_lambda_functions.sh
cd shared
./build_lambda_layer.sh

# Deploy CDK stack
cd cdk
cdk deploy ALBMonitorStack \
  -c elbTargetGroupArn="<PTG_ARN>" \
  --parameters elbArn="<ALB_ARN>" \
  --parameters elbListenerArn="<LISTENER_ARN>"
```

## Prerequisites

- ALB with weighted target group routing configured
- PTG weight=100, STG weight=0 initially
- AWS CDK installed and configured

## Real-World Performance

Blog post demo showed:
- PTG: 2 instances, max 60k req/min per instance
- Alarm: 50k req/min threshold
- Peak shed: 25% to STG during autoscaling
- Result: Stayed under 60k limit (max 57,846), prevented overload
