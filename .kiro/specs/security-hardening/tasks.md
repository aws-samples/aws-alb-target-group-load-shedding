# Security Hardening - Implementation Tasks

## Phase 1: IAM Least Privilege

- [ ] 1. Update ELB permissions
  - [ ] 1.1 Remove `ElasticLoadBalancingFullAccess` managed policy from ALBAlarmLambdaRole
  - [ ] 1.2 Remove `ElasticLoadBalancingFullAccess` managed policy from ALBSQSMessageLambdaRole
  - [ ] 1.3 Add inline policy with `elasticloadbalancing:DescribeRules`
  - [ ] 1.4 Add inline policy with `elasticloadbalancing:ModifyRule`
  - [ ] 1.5 Add inline policy with `elasticloadbalancing:ModifyListener`
  - [ ] 1.6 Scope resources to listener/listener-rule ARN patterns

- [ ] 2. Update CloudWatch Logs permissions
  - [ ] 2.1 Replace `Resource: "*"` with specific log group ARN for ALBAlarmLambda
  - [ ] 2.2 Replace `Resource: "*"` with specific log group ARN for ALBSQSMessageLambda
  - [ ] 2.3 Use `!Sub` or CDK intrinsic functions for ARN construction

## Phase 2: Dead Letter Queue

- [ ] 3. Create DLQ
  - [ ] 3.1 Add DLQ resource with 14-day retention
  - [ ] 3.2 Enable SQS managed encryption on DLQ
  - [ ] 3.3 Configure main queue redrive policy with maxReceiveCount=3
  - [ ] 3.4 Add CloudWatch alarm for DLQ messages > 0
  - [ ] 3.5 Update IAM policies to allow DLQ access

## Phase 3: Lambda Configuration

- [ ] 4. Add Lambda timeouts
  - [ ] 4.1 Set ALBAlarmLambda timeout to 30 seconds
  - [ ] 4.2 Set ALBSQSMessageLambda timeout to 30 seconds
  - [ ] 4.3 Verify SQS visibility timeout > Lambda timeout

## Phase 4: Encryption

- [ ] 5. Enable encryption at rest
  - [ ] 5.1 Enable SQS managed encryption on main queue
  - [ ] 5.2 Verify Lambda environment variable encryption (default enabled)
  - [ ] 5.3 Document encryption configuration in README

## Phase 5: Resource Naming

- [ ] 6. Fix hardcoded names
  - [ ] 6.1 Remove hardcoded `function_name` from ALBAlarmLambda (let CDK generate)
  - [ ] 6.2 Remove hardcoded `function_name` from ALBSQSMessageLambda
  - [ ] 6.3 Remove hardcoded `queue_name` from SQS queue
  - [ ] 6.4 Update any references to hardcoded names

## Phase 6: Validation

- [ ] 7. Test security changes
  - [ ] 7.1 Run `cdk synth` and verify CloudFormation
  - [ ] 7.2 Deploy to test environment
  - [ ] 7.3 Verify Lambda can still modify ELB rules
  - [ ] 7.4 Verify Lambda can write to CloudWatch Logs
  - [ ] 7.5 Test DLQ by forcing message failure
  - [ ] 7.6 Verify DLQ alarm triggers

## Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1 | 1-2 | 1-2h | ⬜ Not Started |
| 2 | 3 | 1h | ⬜ Not Started |
| 3 | 4 | 0.5h | ⬜ Not Started |
| 4 | 5 | 0.5h | ⬜ Not Started |
| 5 | 6 | 1h | ⬜ Not Started |
| 6 | 7 | 1-2h | ⬜ Not Started |

**Total Estimated Effort:** 4-6 hours
**Total Sub-tasks:** 28
