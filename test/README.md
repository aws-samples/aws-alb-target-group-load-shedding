# Testing Infrastructure

This directory contains infrastructure and procedures for **integration testing** the ALB Target Group Load Shedding solution with real AWS resources.

## Integration Testing vs Unit Testing

**Unit Tests** (`source/lambda/shared/elb_load_monitor/tests/`, `source/lambda/tests/`, `cdk/test_cdk/`):
- Test isolated components with mocks
- Fast execution (seconds)
- 98% code coverage
- Run automatically via pytest

**Integration Tests** (this directory):
- Test complete system with REAL AWS resources
- Deploy actual ALB, Lambda, SQS, CloudWatch
- Validate end-to-end functionality
- Manual execution with real AWS costs
- Validates the system works in production-like environment

## Prerequisites

- AWS CLI configured with credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.13 or later

## Quick Start

### 1. Deploy Test ALB Infrastructure

```bash
# Deploy the prerequisite ALB, target groups, and listener
aws cloudformation create-stack \
  --stack-name ALBTestPrerequisites \
  --template-body file://alb-prerequisites.yaml \
  --region us-east-1 \
  --tags Key=Purpose,Value=Testing Key=AutoDelete,Value=true

# Wait for completion
aws cloudformation wait stack-create-complete \
  --stack-name ALBTestPrerequisites \
  --region us-east-1
```

### 2. Get Stack Outputs

```bash
aws cloudformation describe-stacks \
  --stack-name ALBTestPrerequisites \
  --region us-east-1 \
  --query 'Stacks[0].Outputs'
```

### 3. Deploy Load Shedding Stack

```bash
cd ../cdk

# Bootstrap CDK (first time only)
cdk bootstrap -c elbTargetGroupArn="<PRIMARY_TG_ARN>"

# Deploy the monitoring stack
cdk deploy ALBMonitorStack \
  -c elbTargetGroupArn="<PRIMARY_TG_ARN>" \
  --parameters elbArn="<ALB_ARN>" \
  --parameters elbListenerArn="<LISTENER_ARN>" \
  --require-approval never
```

### 4. Test Load Shedding

```bash
# Trigger alarm to ALARM state
aws cloudwatch set-alarm-state \
  --alarm-name ALBTargetGroupAlarm \
  --state-value ALARM \
  --state-reason "Manual test" \
  --region us-east-1

# Wait 5 seconds, then check weights
sleep 5
aws elbv2 describe-rules \
  --listener-arn "<LISTENER_ARN>" \
  --region us-east-1 \
  --query 'Rules[0].Actions[0].ForwardConfig.TargetGroups'

# Expected: PTG weight decreased by 5%, STG increased by 5%
```

### 5. Test Restore

```bash
# Set alarm to OK state
aws cloudwatch set-alarm-state \
  --alarm-name ALBTargetGroupAlarm \
  --state-value OK \
  --state-reason "Manual test restore" \
  --region us-east-1

# Wait 2 minutes for restore message delay
sleep 120

# Check weights
aws elbv2 describe-rules \
  --listener-arn "<LISTENER_ARN>" \
  --region us-east-1 \
  --query 'Rules[0].Actions[0].ForwardConfig.TargetGroups'

# Expected: PTG weight increased by 5%, STG decreased by 5%
```

### 6. Check Lambda Logs

```bash
# View ALBAlarmLambda logs
aws logs tail /aws/lambda/ALBAlarmLambda \
  --region us-east-1 \
  --since 10m \
  --follow

# View ALBSQSMessageLambda logs
aws logs tail /aws/lambda/ALBSQSMessageLambda \
  --region us-east-1 \
  --since 10m \
  --follow
```

## Cleanup

### Delete Load Shedding Stack

```bash
cd ../cdk
cdk destroy ALBMonitorStack \
  -c elbTargetGroupArn="<PRIMARY_TG_ARN>" \
  --force
```

### Delete Test Infrastructure

```bash
aws cloudformation delete-stack \
  --stack-name ALBTestPrerequisites \
  --region us-east-1

# Wait for deletion
aws cloudformation wait stack-delete-complete \
  --stack-name ALBTestPrerequisites \
  --region us-east-1
```

## Test Infrastructure Details

The `alb-prerequisites.yaml` template creates:

- **Application Load Balancer** (`alb-test-loadshed`)
  - Internet-facing
  - HTTP listener on port 80
  - Weighted target group routing

- **Primary Target Group** (`alb-test-ptg`)
  - Initial weight: 100
  - HTTP health checks

- **Shedding Target Group** (`alb-test-stg`)
  - Initial weight: 0
  - HTTP health checks

- **Security Group**
  - Allows inbound HTTP (port 80) from anywhere

## Expected Behavior

### Load Shedding Cycle
1. CloudWatch alarm enters ALARM state
2. EventBridge triggers ALBAlarmLambda
3. Lambda sheds 5% from PTG to STG
4. SQS message queued with 60s delay
5. ALBSQSMessageLambda processes message
6. If still in ALARM, shed another 5%
7. Repeat until max shed limit or alarm clears

### Restore Cycle
1. CloudWatch alarm enters OK state
2. EventBridge triggers ALBAlarmLambda
3. Lambda prepares restore
4. SQS message queued with 120s delay
5. ALBSQSMessageLambda processes message
6. Restore 5% from STG to PTG
7. Repeat until PTG=100, STG=0

## Troubleshooting

### Alarm stays in INSUFFICIENT_DATA
- Normal when no traffic to target groups
- Add targets or generate test traffic
- Manually set alarm state for testing

### Weights not changing
- Check Lambda logs for errors
- Verify IAM permissions
- Check EventBridge rule is enabled

### SQS messages not processing
- Check Lambda event source mapping
- Verify SQS queue permissions
- Check Lambda execution role

## Cost Estimate

Running this test infrastructure:
- ALB: ~$0.025/hour (~$18/month)
- Lambda: Free tier eligible
- SQS: Free tier eligible
- CloudWatch: Free tier eligible

**Recommendation:** Delete resources after testing to avoid charges.
