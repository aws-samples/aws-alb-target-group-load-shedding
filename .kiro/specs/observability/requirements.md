# Observability - Requirements

## Overview

Add comprehensive monitoring, tracing, and logging to the ALB Target Group Load Shedding solution.

## Functional Requirements

### 1. CloudWatch Alarms

#### 1.1 Lambda Error Alarms
- **As an** operator
- **I want** alerts when Lambda functions fail
- **So that** I can respond to issues quickly

**Acceptance Criteria:**
- [ ] Alarm for ALBAlarmLambda errors > 0
- [ ] Alarm for ALBSQSMessageLambda errors > 0
- [ ] Alarm for Lambda throttling
- [ ] Alarm for Lambda duration > 80% of timeout

### 2. X-Ray Tracing

#### 2.1 Distributed Tracing
- **As a** developer
- **I want** request tracing across services
- **So that** I can debug issues and understand latency

**Acceptance Criteria:**
- [ ] Enable X-Ray tracing on ALBAlarmLambda
- [ ] Enable X-Ray tracing on ALBSQSMessageLambda
- [ ] Add X-Ray SDK to Lambda layer
- [ ] Trace boto3 calls to ELB and SQS

### 3. Structured Logging

#### 3.1 JSON Logging
- **As an** operator
- **I want** structured JSON logs
- **So that** I can query and analyze logs efficiently

**Acceptance Criteria:**
- [ ] Replace print/logger with structured JSON format
- [ ] Include correlation IDs across Lambda invocations
- [ ] Include alarm name, action, weights in log entries
- [ ] Use AWS Lambda Powertools for logging

### 4. CloudWatch Dashboard

#### 4.1 Operational Dashboard
- **As an** operator
- **I want** a single dashboard for monitoring
- **So that** I can see system health at a glance

**Acceptance Criteria:**
- [ ] Lambda invocation count widget
- [ ] Lambda error rate widget
- [ ] Lambda duration widget
- [ ] SQS queue depth widget
- [ ] DLQ message count widget
- [ ] Target group weight history widget

### 5. Custom Metrics

#### 5.1 Business Metrics
- **As an** operator
- **I want** custom metrics for shedding operations
- **So that** I can track business-level behavior

**Acceptance Criteria:**
- [ ] Metric: ShedOperationCount
- [ ] Metric: RestoreOperationCount
- [ ] Metric: CurrentPTGWeight
- [ ] Metric: CurrentSTGWeight

## Non-Functional Requirements

### 6. Performance
- Logging overhead < 10ms per invocation
- X-Ray sampling rate configurable

### 7. Cost
- Use metric filters where possible to reduce costs
- Configure log retention (14 days default)

## Estimated Effort
3-4 hours
