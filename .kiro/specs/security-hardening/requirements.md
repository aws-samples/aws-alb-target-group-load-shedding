# Security Hardening - Requirements

## Overview

Address critical security vulnerabilities in the ALB Target Group Load Shedding solution including IAM least privilege, encryption, and failure handling.

## Functional Requirements

### 1. IAM Least Privilege

#### 1.1 ELB Permissions
- **As a** security engineer
- **I want** minimal ELB permissions
- **So that** blast radius of any compromise is limited

**Acceptance Criteria:**
- [ ] Replace `ElasticLoadBalancingFullAccess` managed policy
- [ ] Add inline policy with only required actions:
  - `elasticloadbalancing:DescribeRules`
  - `elasticloadbalancing:ModifyRule`
  - `elasticloadbalancing:ModifyListener`
- [ ] Scope to specific ALB ARN where possible

#### 1.2 CloudWatch Logs Permissions
- **As a** security engineer
- **I want** scoped log permissions
- **So that** Lambda can only write to its own log groups

**Acceptance Criteria:**
- [ ] Replace `Resource: "*"` with specific log group ARNs
- [ ] Use `!Sub` to reference stack-specific log groups

### 2. Dead Letter Queue

#### 2.1 DLQ Configuration
- **As an** operator
- **I want** failed messages captured
- **So that** I can investigate and retry failures

**Acceptance Criteria:**
- [ ] Create DLQ with 14-day retention
- [ ] Configure main queue redrive policy (maxReceiveCount: 3)
- [ ] Add CloudWatch alarm for DLQ message count > 0

### 3. Lambda Timeout

#### 3.1 Explicit Timeout
- **As an** operator
- **I want** Lambda timeouts configured
- **So that** runaway executions are terminated

**Acceptance Criteria:**
- [ ] Set ALBAlarmLambda timeout to 30 seconds
- [ ] Set ALBSQSMessageLambda timeout to 30 seconds

### 4. Encryption at Rest

#### 4.1 SQS Encryption
- **As a** security engineer
- **I want** SQS messages encrypted
- **So that** data is protected at rest

**Acceptance Criteria:**
- [ ] Enable SQS server-side encryption (SSE-SQS or SSE-KMS)
- [ ] Document encryption configuration

#### 4.2 Lambda Environment Encryption
- **As a** security engineer
- **I want** Lambda env vars encrypted
- **So that** configuration is protected

**Acceptance Criteria:**
- [ ] Enable Lambda environment variable encryption
- [ ] Use AWS managed key or customer managed key

### 5. Function Naming

#### 5.1 Stack-Prefixed Names
- **As a** developer
- **I want** unique function names per stack
- **So that** multiple stacks can deploy to same account

**Acceptance Criteria:**
- [ ] Use stack name prefix for Lambda functions
- [ ] Use stack name prefix for SQS queues
- [ ] Or let CDK auto-generate unique names

## Non-Functional Requirements

### 6. Backward Compatibility
- Existing deployments must be updatable without recreation
- CloudFormation parameters must remain compatible

## Estimated Effort
4-6 hours
