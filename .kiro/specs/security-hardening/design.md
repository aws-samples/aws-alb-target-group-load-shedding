# Security Hardening - Design Document

## 1. IAM Least Privilege

### 1.1 Current State (Insecure)

```python
iam.ManagedPolicy.from_aws_managed_policy_name("ElasticLoadBalancingFullAccess")
```

### 1.2 Target State

```python
iam.PolicyStatement(
    effect=iam.Effect.ALLOW,
    actions=[
        "elasticloadbalancing:DescribeRules",
        "elasticloadbalancing:ModifyRule",
        "elasticloadbalancing:ModifyListener"
    ],
    resources=[
        f"arn:aws:elasticloadbalancing:{region}:{account}:listener/*",
        f"arn:aws:elasticloadbalancing:{region}:{account}:listener-rule/*"
    ]
)
```

### 1.3 CloudWatch Logs Scoping

```python
iam.PolicyStatement(
    effect=iam.Effect.ALLOW,
    actions=[
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
    ],
    resources=[
        f"arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function_name}:*"
    ]
)
```

## 2. Dead Letter Queue

### 2.1 Architecture

```
Main Queue ──(3 failures)──> DLQ ──> CloudWatch Alarm
```

### 2.2 Implementation

```python
dlq = sqs.Queue(
    self, "ALBMonitorDLQ",
    queue_name=f"{stack_name}-dlq",
    retention_period=Duration.days(14),
    encryption=sqs.QueueEncryption.SQS_MANAGED
)

main_queue = sqs.Queue(
    self, "ALBMonitorQueue",
    queue_name=f"{stack_name}-queue",
    encryption=sqs.QueueEncryption.SQS_MANAGED,
    dead_letter_queue=sqs.DeadLetterQueue(
        max_receive_count=3,
        queue=dlq
    )
)

# DLQ Alarm
cloudwatch.Alarm(
    self, "DLQAlarm",
    metric=dlq.metric_approximate_number_of_messages_visible(),
    threshold=1,
    evaluation_periods=1,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD
)
```

## 3. Lambda Timeout

### 3.1 Implementation

```python
_lambda.Function(
    self, "ALBAlarmLambda",
    timeout=Duration.seconds(30),
    # ... other props
)
```

### 3.2 Rationale

- Default 3 seconds too short for ELB API calls
- 30 seconds allows for API retries
- SQS visibility timeout should be > Lambda timeout

## 4. Encryption at Rest

### 4.1 SQS Encryption

```python
sqs.Queue(
    self, "Queue",
    encryption=sqs.QueueEncryption.SQS_MANAGED  # or KMS_MANAGED
)
```

### 4.2 Lambda Environment Encryption

Lambda environment variables are encrypted by default with AWS managed key. For customer managed key:

```python
_lambda.Function(
    self, "Function",
    environment_encryption=kms.Key(self, "EnvKey")
)
```

## 5. Stack-Prefixed Naming

### 5.1 Current (Hardcoded)

```python
function_name="ALBAlarmLambda"
queue_name="alb_target_group_monitor_queue"
```

### 5.2 Target (Dynamic)

```python
# Option 1: Stack prefix
function_name=f"{self.stack_name}-alarm-lambda"

# Option 2: Let CDK generate (recommended)
# Omit function_name parameter entirely
```

## 6. Estimated Effort

| Task | Effort |
|------|--------|
| IAM least privilege | 1-2h |
| Dead Letter Queue | 1h |
| Lambda timeout | 0.5h |
| Encryption | 0.5h |
| Function naming | 1h |
| Testing | 1-2h |
| **Total** | **4-6h** |
