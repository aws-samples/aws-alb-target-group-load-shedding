# Testing Improvements - Requirements

## Overview

Improve test coverage for the ALB Target Group Load Shedding solution from ~30% to 80%+ by migrating to pytest and adding comprehensive test coverage.

## Functional Requirements

### 1. Test Framework Migration

#### 1.1 Replace Deprecated Framework
- **As a** developer
- **I want** to use pytest instead of unittest/nose
- **So that** I have access to modern testing features and active maintenance

**Acceptance Criteria:**
- [ ] pytest>=8.0.0 installed as dev dependency
- [ ] pytest-cov>=4.1.0 for coverage reporting
- [ ] pytest-mock>=3.12.0 for enhanced mocking
- [ ] moto>=5.0.0 for AWS service mocking
- [ ] freezegun>=1.4.0 for time mocking
- [ ] nose removed from setup.py
- [ ] Existing tests converted to pytest style

### 2. Lambda Handler Tests

#### 2.1 ALBAlarmLambda Handler Tests
- **As a** developer
- **I want** tests for the EventBridge alarm handler
- **So that** I can verify alarm events are processed correctly

**Acceptance Criteria:**
- [ ] Test handler processes ALARM state correctly
- [ ] Test handler processes OK state correctly
- [ ] Test handler rejects invalid event types
- [ ] Test handler fails gracefully with missing env vars

#### 2.2 ALBSQSMessageLambda Handler Tests
- **As a** developer
- **I want** tests for the SQS message handler
- **So that** I can verify follow-up messages are processed correctly

**Acceptance Criteria:**
- [ ] Test SQS message triggers shed action
- [ ] Test SQS message triggers restore action
- [ ] Test handler handles empty SQS records
- [ ] Test handler handles malformed JSON

### 3. Error Handling Tests

#### 3.1 AWS API Error Handling
- **As a** developer
- **I want** tests for error scenarios
- **So that** I can verify the system handles failures gracefully

**Acceptance Criteria:**
- [ ] Test handling of boto3 ClientError
- [ ] Test handling of missing listener
- [ ] Test handling of invalid target group ARN
- [ ] Test SQS send failure handling
- [ ] Test handling when alarm doesn't exist

### 4. Message Serialization Tests

#### 4.1 JSON Serialization
- **As a** developer
- **I want** tests for message serialization
- **So that** I can verify data integrity across Lambda invocations

**Acceptance Criteria:**
- [ ] Test message serialization (to_json)
- [ ] Test message deserialization (from_json)
- [ ] Test serialize -> deserialize roundtrip preserves data
- [ ] Test ALBAlarmEvent initialization

### 5. Edge Case Tests

#### 5.1 Algorithm Edge Cases
- **As a** developer
- **I want** tests for edge cases in shedding/restore algorithms
- **So that** I can verify correct behavior at boundaries

**Acceptance Criteria:**
- [ ] Test shedding when at maxElbShedPercent
- [ ] Test shedding caps at maxElbShedPercent
- [ ] Test restore when STG has 0 weight
- [ ] Test shed distributes across 3+ target groups
- [ ] Test restore handles remainder correctly
- [ ] Test weights never go negative

### 6. CDK Infrastructure Tests

#### 6.1 Stack Resource Tests
- **As a** developer
- **I want** tests for CDK stack resources
- **So that** I can verify infrastructure is created correctly

**Acceptance Criteria:**
- [ ] Test stack creates both Lambda functions
- [ ] Test stack creates SQS queue
- [ ] Test stack creates CloudWatch alarm
- [ ] Test stack creates EventBridge rule
- [ ] Test Lambda environment variables are set
- [ ] Test IAM roles have required permissions
- [ ] Test SQS has Dead Letter Queue (after DLQ added)

### 7. Integration Tests

#### 7.1 End-to-End Flow Tests
- **As a** developer
- **I want** integration tests with mocked AWS services
- **So that** I can verify the complete shed/restore cycle

**Acceptance Criteria:**
- [ ] Test complete shed -> restore cycle with mocked AWS
- [ ] Test multiple shed actions reach max limit
- [ ] Test restore returns to 100% PTG

## Non-Functional Requirements

### 8. Coverage Requirements

#### 8.1 Coverage Thresholds
- Overall coverage must reach 80%+
- `elb_listener_rule.py`: 90%
- `alb_listener_rules_handler.py`: 85%
- `alb_alarm_messages.py`: 80%
- Lambda handlers: 75%
- CDK stack: 70%

### 9. Test Configuration

#### 9.1 pytest Configuration
- pytest.ini with test paths configured
- .coveragerc with exclusion rules
- Coverage reports in HTML and terminal formats
- Coverage threshold enforcement (--cov-fail-under=80)

## Dependencies

- Requires existing codebase (alb-target-group-load-shedding spec complete)
- CDK tests require CDK v2 migration (cdk-modernization spec)
