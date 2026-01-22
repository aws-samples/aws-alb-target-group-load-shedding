# Observability - Implementation Tasks

## Phase 1: CloudWatch Alarms

- [ ] 1. Add Lambda error alarms
  - [ ] 1.1 Create alarm for ALBAlarmLambda errors > 0
  - [ ] 1.2 Create alarm for ALBSQSMessageLambda errors > 0
  - [ ] 1.3 Create alarm for Lambda throttling
  - [ ] 1.4 Create alarm for Lambda duration > 80% timeout

## Phase 2: X-Ray Tracing

- [ ] 2. Enable X-Ray
  - [ ] 2.1 Add `tracing=Tracing.ACTIVE` to ALBAlarmLambda
  - [ ] 2.2 Add `tracing=Tracing.ACTIVE` to ALBSQSMessageLambda
  - [ ] 2.3 Add X-Ray IAM permissions to Lambda roles
  - [ ] 2.4 Add `aws-xray-sdk` to Lambda layer requirements
  - [ ] 2.5 Add `patch_all()` to Lambda handlers
  - [ ] 2.6 Add `@xray_recorder.capture` decorators to key functions

## Phase 3: Structured Logging

- [ ] 3. Implement structured logging
  - [ ] 3.1 Add `aws-lambda-powertools` to Lambda layer requirements
  - [ ] 3.2 Replace logger in `alb_alarm_lambda_handler.py` with Powertools Logger
  - [ ] 3.3 Replace logger in `alb_alarm_check_lambda_handler.py` with Powertools Logger
  - [ ] 3.4 Replace logger in `alb_listener_rules_handler.py` with Powertools Logger
  - [ ] 3.5 Add correlation ID to SQS messages
  - [ ] 3.6 Add structured fields (alarm_name, action, weights) to log entries
  - [ ] 3.7 Add `@logger.inject_lambda_context` decorators

## Phase 4: CloudWatch Dashboard

- [ ] 4. Create operational dashboard
  - [ ] 4.1 Create CloudWatch Dashboard resource in CDK
  - [ ] 4.2 Add Lambda invocation count widget
  - [ ] 4.3 Add Lambda error rate widget
  - [ ] 4.4 Add Lambda duration widget
  - [ ] 4.5 Add SQS queue depth widget
  - [ ] 4.6 Add DLQ message count widget

## Phase 5: Custom Metrics

- [ ] 5. Add business metrics
  - [ ] 5.1 Add Powertools Metrics to Lambda handlers
  - [ ] 5.2 Emit ShedOperationCount metric
  - [ ] 5.3 Emit RestoreOperationCount metric
  - [ ] 5.4 Emit PTGWeight metric
  - [ ] 5.5 Add custom metrics to dashboard

## Phase 6: Log Configuration

- [ ] 6. Configure log retention
  - [ ] 6.1 Set CloudWatch Logs retention to 14 days for ALBAlarmLambda
  - [ ] 6.2 Set CloudWatch Logs retention to 14 days for ALBSQSMessageLambda

## Phase 7: Validation

- [ ] 7. Test observability
  - [ ] 7.1 Deploy and trigger alarm
  - [ ] 7.2 Verify X-Ray traces appear in console
  - [ ] 7.3 Verify structured logs in CloudWatch Logs Insights
  - [ ] 7.4 Verify dashboard displays correctly
  - [ ] 7.5 Verify custom metrics in CloudWatch Metrics

## Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1 | 1 | 0.5h | ⬜ Not Started |
| 2 | 2 | 1h | ⬜ Not Started |
| 3 | 3 | 1h | ⬜ Not Started |
| 4 | 4 | 0.5h | ⬜ Not Started |
| 5 | 5 | 0.5h | ⬜ Not Started |
| 6 | 6 | 0.25h | ⬜ Not Started |
| 7 | 7 | 0.5h | ⬜ Not Started |

**Total Estimated Effort:** 3-4 hours
**Total Sub-tasks:** 32
