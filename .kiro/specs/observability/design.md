# Observability - Design Document

## 1. CloudWatch Alarms

### 1.1 Lambda Error Alarm

```python
cloudwatch.Alarm(
    self, "ALBAlarmLambdaErrors",
    metric=alb_alarm_lambda.metric_errors(),
    threshold=1,
    evaluation_periods=1,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
    alarm_description="ALBAlarmLambda function errors"
)
```

### 1.2 Lambda Duration Alarm

```python
cloudwatch.Alarm(
    self, "ALBAlarmLambdaDuration",
    metric=alb_alarm_lambda.metric_duration(),
    threshold=24000,  # 80% of 30s timeout
    evaluation_periods=3,
    comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_THRESHOLD,
    alarm_description="ALBAlarmLambda approaching timeout"
)
```

## 2. X-Ray Tracing

### 2.1 Lambda Configuration

```python
_lambda.Function(
    self, "ALBAlarmLambda",
    tracing=_lambda.Tracing.ACTIVE,
    # ... other props
)
```

### 2.2 Lambda Code Changes

```python
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all

patch_all()  # Patches boto3, requests, etc.

@xray_recorder.capture('handle_alarm')
def handler(event, context):
    # ... existing code
```

### 2.3 IAM Permissions

```python
iam.PolicyStatement(
    effect=iam.Effect.ALLOW,
    actions=[
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords"
    ],
    resources=["*"]
)
```

## 3. Structured Logging

### 3.1 AWS Lambda Powertools

```python
from aws_lambda_powertools import Logger

logger = Logger(service="alb-load-shedding")

@logger.inject_lambda_context
def handler(event, context):
    logger.info("Processing alarm", extra={
        "alarm_name": alarm_name,
        "action": action,
        "ptg_weight": ptg_weight
    })
```

### 3.2 Log Format

```json
{
    "level": "INFO",
    "location": "handler:45",
    "message": "Processing alarm",
    "timestamp": "2025-01-22T10:30:00.000Z",
    "service": "alb-load-shedding",
    "cold_start": false,
    "function_name": "ALBAlarmLambda",
    "function_request_id": "abc-123",
    "alarm_name": "ALBTargetGroupAlarm",
    "action": "SHED",
    "ptg_weight": 95
}
```

### 3.3 Correlation ID

```python
# Pass correlation ID via SQS message
message["correlation_id"] = context.aws_request_id

# In SQS handler
logger.append_keys(correlation_id=message.get("correlation_id"))
```

## 4. CloudWatch Dashboard

### 4.1 Dashboard Definition

```python
dashboard = cloudwatch.Dashboard(
    self, "ALBLoadSheddingDashboard",
    dashboard_name="ALB-Load-Shedding"
)

dashboard.add_widgets(
    cloudwatch.GraphWidget(
        title="Lambda Invocations",
        left=[
            alb_alarm_lambda.metric_invocations(),
            alb_sqs_lambda.metric_invocations()
        ]
    ),
    cloudwatch.GraphWidget(
        title="Lambda Errors",
        left=[
            alb_alarm_lambda.metric_errors(),
            alb_sqs_lambda.metric_errors()
        ]
    ),
    cloudwatch.GraphWidget(
        title="SQS Queue Depth",
        left=[main_queue.metric_approximate_number_of_messages_visible()]
    )
)
```

## 5. Custom Metrics

### 5.1 Emit Metrics from Lambda

```python
from aws_lambda_powertools import Metrics
from aws_lambda_powertools.metrics import MetricUnit

metrics = Metrics(namespace="ALBLoadShedding", service="alb-load-shedding")

@metrics.log_metrics
def handler(event, context):
    metrics.add_metric(name="ShedOperationCount", unit=MetricUnit.Count, value=1)
    metrics.add_metric(name="PTGWeight", unit=MetricUnit.Percent, value=ptg_weight)
```

## 6. Dependencies

Add to Lambda layer:
```
aws-lambda-powertools>=2.30.0
aws-xray-sdk>=2.12.0
```

## 7. Estimated Effort

| Task | Effort |
|------|--------|
| CloudWatch alarms | 1h |
| X-Ray tracing | 1h |
| Structured logging | 1h |
| Dashboard | 0.5h |
| Custom metrics | 0.5h |
| **Total** | **3-4h** |
