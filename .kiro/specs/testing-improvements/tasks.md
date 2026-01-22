# Testing Improvements - Implementation Tasks

## Phase 1: Test Framework Migration

- [ ] 1. Test framework setup
  - [ ] 1.1 Create `source/lambda/shared/requirements-dev.txt` with pytest dependencies
  - [ ] 1.2 Create `pytest.ini` with test paths and coverage configuration
  - [ ] 1.3 Create `.coveragerc` with exclusion rules
  - [ ] 1.4 Remove `nose` from `source/lambda/shared/setup.py`
  - [ ] 1.5 Convert existing tests to pytest style (remove unittest.TestCase inheritance)

## Phase 2: Lambda Handler Tests (Priority 1 - 4h)

- [ ] 2. ALBAlarmLambda handler tests
  - [ ] 2.1 Create `source/lambda/tests/` directory
  - [ ] 2.2 Create `test_alb_alarm_lambda_handler.py`
  - [ ] 2.3 Test handler processes ALARM state correctly
  - [ ] 2.4 Test handler processes OK state correctly
  - [ ] 2.5 Test handler rejects invalid event types
  - [ ] 2.6 Test handler fails gracefully with missing env vars

- [ ] 3. ALBSQSMessageLambda handler tests
  - [ ] 3.1 Create `test_alb_alarm_check_lambda_handler.py`
  - [ ] 3.2 Test SQS message triggers shed action
  - [ ] 3.3 Test SQS message triggers restore action
  - [ ] 3.4 Test handler handles empty SQS records
  - [ ] 3.5 Test handler handles malformed JSON

## Phase 3: Error Handling Tests (Priority 2 - 2h)

- [ ] 4. Error handling tests
  - [ ] 4.1 Create `source/lambda/shared/elb_load_monitor/tests/test_error_handling.py`
  - [ ] 4.2 Test handling of boto3 ClientError
  - [ ] 4.3 Test handling of missing listener
  - [ ] 4.4 Test handling of invalid target group ARN
  - [ ] 4.5 Test SQS send failure handling
  - [ ] 4.6 Test handling when alarm doesn't exist

## Phase 4: Message Serialization Tests (Priority 3 - 1h)

- [ ] 5. Message serialization tests
  - [ ] 5.1 Create `source/lambda/shared/elb_load_monitor/tests/test_alb_alarm_messages.py`
  - [ ] 5.2 Test message serialization (to_json)
  - [ ] 5.3 Test message deserialization (from_json)
  - [ ] 5.4 Test serialize -> deserialize roundtrip preserves data
  - [ ] 5.5 Test ALBAlarmEvent initialization

## Phase 5: Edge Case Tests (Priority 4 - 2h)

- [ ] 6. Edge case tests
  - [ ] 6.1 Expand `test_elb_listener_rule.py` with edge cases
  - [ ] 6.2 Test shedding when at maxElbShedPercent
  - [ ] 6.3 Test shedding caps at maxElbShedPercent
  - [ ] 6.4 Test restore when STG has 0 weight
  - [ ] 6.5 Test shed distributes across 3+ target groups
  - [ ] 6.6 Test restore handles remainder correctly
  - [ ] 6.7 Test weights never go negative

## Phase 6: CDK Tests (Priority 5 - 3h)

- [ ] 7. CDK infrastructure tests
  - [ ] 7.1 Create `cdk/tests/` directory
  - [ ] 7.2 Create `test_alb_monitor_stack.py`
  - [ ] 7.3 Test stack creates both Lambda functions
  - [ ] 7.4 Test stack creates SQS queue
  - [ ] 7.5 Test stack creates CloudWatch alarm
  - [ ] 7.6 Test stack creates EventBridge rule
  - [ ] 7.7 Test Lambda environment variables are set
  - [ ] 7.8 Test IAM roles have required permissions
  - [ ] 7.9 Test SQS has Dead Letter Queue configured *(after DLQ added)*

## Phase 7: Integration Tests (Priority 6 - 4h)

- [ ] 8. Integration tests
  - [ ] 8.1 Create `source/lambda/tests/integration/` directory
  - [ ] 8.2 Create `test_end_to_end.py` with moto mocks
  - [ ] 8.3 Test complete shed -> restore cycle with mocked AWS services
  - [ ] 8.4 Test multiple shed actions reach max limit
  - [ ] 8.5 Test restore returns to 100% PTG

## Phase 8: Coverage Validation

- [ ] 9. Coverage validation
  - [ ] 9.1 Run pytest with coverage
  - [ ] 9.2 Verify coverage meets 80% threshold
  - [ ] 9.3 Generate HTML coverage report
  - [ ] 9.4 Document any coverage gaps with justification

## Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1 | 1 | 2h | ⬜ Not Started |
| 2 | 2-3 | 4h | ⬜ Not Started |
| 3 | 4 | 2h | ⬜ Not Started |
| 4 | 5 | 1h | ⬜ Not Started |
| 5 | 6 | 2h | ⬜ Not Started |
| 6 | 7 | 3h | ⬜ Not Started |
| 7 | 8 | 4h | ⬜ Not Started |
| 8 | 9 | - | ⬜ Not Started |

**Total Estimated Effort:** 16 hours
**Total Sub-tasks:** 46
