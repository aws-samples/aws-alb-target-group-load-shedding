# CDK Modernization - Requirements

## Overview

Migrate the ALB Target Group Load Shedding solution from deprecated AWS CDK v1 to CDK v2, update Lambda runtime to Python 3.12+, and address critical security and technical debt issues.

## Functional Requirements

### 1. CDK v2 Migration

#### 1.1 Update CDK Dependencies
- **As a** developer
- **I want** to migrate from CDK v1 to CDK v2
- **So that** I have access to security patches and new features

**Acceptance Criteria:**
- [ ] Replace `aws-cdk.core` with `aws-cdk-lib`
- [ ] Replace individual `aws-cdk.aws-*` packages with `aws-cdk-lib`
- [ ] Update `constructs` to v10+
- [ ] Remove deprecated feature flags from `cdk.json`
- [ ] Update all import statements in stack code
- [ ] Verify `cdk synth` produces valid CloudFormation

### 2. Lambda Runtime Update

#### 2.1 Update Python Runtime
- **As a** developer
- **I want** to use Python 3.12+ runtime
- **So that** I have access to security patches and language features

**Acceptance Criteria:**
- [ ] Update Lambda runtime from Python 3.8 to Python 3.12
- [ ] Update Lambda layer compatibility to Python 3.12
- [ ] Verify all code is compatible with Python 3.12
- [ ] Update any deprecated Python syntax

### 3. Dependency Updates

#### 3.1 Update boto3/botocore
- **As a** developer
- **I want** current boto3/botocore versions
- **So that** I have access to latest AWS API features and fixes

**Acceptance Criteria:**
- [ ] Update boto3 to 1.34.0+
- [ ] Update botocore to 1.34.0+
- [ ] Remove unused dependencies (jsii, six)
- [ ] Verify all AWS API calls work with updated SDK

### 4. Security Improvements

#### 4.1 IAM Least Privilege
- **As a** security engineer
- **I want** minimal IAM permissions
- **So that** the blast radius of any compromise is limited

**Acceptance Criteria:**
- [ ] Replace `ElasticLoadBalancingFullAccess` with specific permissions
- [ ] Scope permissions to specific resources where possible
- [ ] Document required permissions

#### 4.2 Add Dead Letter Queue
- **As an** operator
- **I want** failed messages captured in a DLQ
- **So that** I can investigate and retry failed operations

**Acceptance Criteria:**
- [ ] Create DLQ with 14-day retention
- [ ] Configure main queue to use DLQ
- [ ] Set maxReceiveCount for redrive policy

#### 4.3 Add Lambda Timeout
- **As an** operator
- **I want** Lambda functions to have timeouts
- **So that** runaway executions are terminated

**Acceptance Criteria:**
- [ ] Add 30-second timeout to ALBAlarmLambda
- [ ] Add 30-second timeout to ALBSQSMessageLambda

### 5. Code Quality

#### 5.1 Fix Deprecation Warnings
- **As a** developer
- **I want** to remove deprecated code patterns
- **So that** the codebase is maintainable

**Acceptance Criteria:**
- [ ] Replace `logger.warn` with `logger.warning`
- [ ] Use parameterized logging instead of string concatenation
- [ ] Remove unused imports
- [ ] Add `__all__` exports to `__init__.py`

#### 5.2 Add Type Hints
- **As a** developer
- **I want** type annotations
- **So that** I can catch errors earlier and improve IDE support

**Acceptance Criteria:**
- [ ] Add type hints to all public functions
- [ ] Add type hints to class attributes
- [ ] Configure mypy for type checking (optional)

## Non-Functional Requirements

### 6. Backward Compatibility

#### 6.1 API Compatibility
- Existing CloudFormation parameters must remain compatible
- Existing environment variable names must not change
- SQS message format must remain compatible

### 7. Validation

#### 7.1 Deployment Validation
- [ ] `cdk synth` produces valid CloudFormation
- [ ] `cdk deploy` succeeds in test environment
- [ ] Alarm triggers shed behavior correctly
- [ ] Alarm clears restore behavior correctly

## Dependencies

- Requires existing codebase (alb-target-group-load-shedding spec complete)
- Testing improvements spec should be completed after this migration
