# CDK Modernization - Design Document

## 1. Overview

This design document outlines the migration from AWS CDK v1 to CDK v2, runtime updates, and security improvements for the ALB Target Group Load Shedding solution.

## 2. Current State (January 2025)

| Component | Current Version | Status |
|-----------|-----------------|--------|
| AWS CDK | v1 (`aws-cdk.aws-*>=1.107`) | EOL June 2023 |
| Lambda Runtime | Python 3.8 | Deprecated |
| boto3 | 1.16.29 (Dec 2020) | 4+ years old |
| botocore | 1.19.29 (Dec 2020) | 4+ years old |
| constructs | 3.3.75 | CDK v1 only |

## 3. Target State

| Component | Target Version | Notes |
|-----------|----------------|-------|
| AWS CDK | v2 (`aws-cdk-lib>=2.170.0`) | Latest stable |
| Lambda Runtime | Python 3.12 | Current LTS |
| boto3 | 1.34.0+ | Latest |
| botocore | 1.34.0+ | Latest |
| constructs | 10.0.0+ | CDK v2 compatible |

## 4. CDK v2 Migration

### 4.1 Import Changes

**Before (CDK v1):**
```python
from aws_cdk import core as cdk
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk import aws_lambda_event_sources as lambda_event_sources
```

**After (CDK v2):**
```python
from aws_cdk import (
    Stack,
    Duration,
    CfnParameter,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_iam as iam,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_lambda_event_sources as lambda_event_sources,
)
from constructs import Construct
```

### 4.2 Stack Class Changes

**Before:**
```python
class ALBMonitorStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
```

**After:**
```python
class ALBMonitorStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
```

### 4.3 Duration Changes

**Before:**
```python
cdk.Duration.seconds(60)
```

**After:**
```python
Duration.seconds(60)
```

### 4.4 Feature Flags Removal

Remove from `cdk.json`:
```json
{
  "@aws-cdk/core:enableStackNameDuplicates": "true",
  "aws-cdk:enableDiffNoFail": "true",
  "@aws-cdk/core:stackRelativeExports": "true"
}
```

These are default behavior in CDK v2.

## 5. Dependency Updates

### 5.1 cdk/requirements.txt

**Before:**
```
aws-cdk.core>=1.107
aws-cdk.aws-lambda>=1.107
aws-cdk.aws-sqs>=1.107
aws-cdk.aws-iam>=1.107
aws-cdk.aws-events>=1.107
aws-cdk.aws-events-targets>=1.107
aws-cdk.aws-cloudwatch>=1.107
aws-cdk.aws-lambda-event-sources>=1.107
jsii>=1.29.0
six>=1.15.0
```

**After:**
```
aws-cdk-lib>=2.170.0
constructs>=10.0.0
```

### 5.2 source/lambda/shared/requirements.txt

**Before:**
```
boto3>=1.16.29
botocore>=1.19.29
```

**After:**
```
boto3>=1.34.0
botocore>=1.34.0
```

## 6. Lambda Runtime Update

### 6.1 Stack Changes

**Before:**
```python
runtime=_lambda.Runtime.PYTHON_3_8
```

**After:**
```python
runtime=_lambda.Runtime.PYTHON_3_12
```

### 6.2 Layer Compatibility

**Before:**
```python
compatible_runtimes=[
    _lambda.Runtime.PYTHON_3_7,
    _lambda.Runtime.PYTHON_3_8
]
```

**After:**
```python
compatible_runtimes=[
    _lambda.Runtime.PYTHON_3_11,
    _lambda.Runtime.PYTHON_3_12
]
```

## 7. Security Improvements

### 7.1 IAM Least Privilege

**Before:**
```python
iam.ManagedPolicy.from_aws_managed_policy_name("ElasticLoadBalancingFullAccess")
```

**After:**
```python
iam.PolicyStatement(
    effect=iam.Effect.ALLOW,
    actions=[
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:ModifyListener"
    ],
    resources=["*"]  # Can scope to specific ALB ARN
)
```

### 7.2 Dead Letter Queue

```python
dlq = sqs.Queue(
    self, "ALBMonitorDLQ",
    queue_name="alb_target_group_monitor_dlq",
    retention_period=Duration.days(14)
)

main_queue = sqs.Queue(
    self, "ALBMonitorQueue",
    queue_name="alb_target_group_monitor_queue",
    dead_letter_queue=sqs.DeadLetterQueue(
        max_receive_count=3,
        queue=dlq
    )
)
```

### 7.3 Lambda Timeout

```python
_lambda.Function(
    self, "ALBAlarmLambda",
    timeout=Duration.seconds(30),
    # ... other props
)
```

## 8. Code Quality Fixes

### 8.1 Logger Warning

**Before:**
```python
logger.warn("No SQS message")
```

**After:**
```python
logger.warning("No SQS message")
```

### 8.2 Parameterized Logging

**Before:**
```python
logger.info("Processing alarm: " + alarm_name)
```

**After:**
```python
logger.info("Processing alarm: %s", alarm_name)
```

### 8.3 Unused Imports

Remove from `elb_listener_rule.py`:
```python
from re import S  # Unused
```

### 8.4 Module Exports

Add to `elb_load_monitor/__init__.py`:
```python
__all__ = [
    "ALBListenerRulesHandler",
    "ELBListenerRule",
    "ALBAlarmEvent",
    "ALBAlarmStatusMessage",
    "CWAlarmState",
    "ALBAlarmAction",
]
```

## 9. Migration Effort Estimate

| Phase | Effort | Risk |
|-------|--------|------|
| CDK v2 Migration | 4-8 hours | Medium |
| Runtime Update | 1-2 hours | Low |
| Dependency Updates | 2-4 hours | Medium |
| Security Improvements | 2-4 hours | Low |
| Code Quality | 4-6 hours | Low |
| **Total** | **13-24 hours** | |

## 10. Validation Plan

1. Run existing unit tests
2. `cdk synth` produces valid CloudFormation
3. Compare CloudFormation diff (should be minimal)
4. Deploy to test environment
5. Trigger alarm and verify shed behavior
6. Clear alarm and verify restore behavior
7. Verify DLQ captures failed messages
