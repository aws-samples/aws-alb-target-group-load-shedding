# ALB Target Group Load Shedding - Testing Improvements

## Current State

| Metric | Value |
|--------|-------|
| Test Files | 2 |
| Test Methods | 12 |
| Estimated Coverage | ~30% |
| Framework | unittest + nose (deprecated) |

## Target State

| Metric | Value |
|--------|-------|
| Test Files | 8+ |
| Test Methods | 40+ |
| Target Coverage | 80%+ |
| Framework | pytest + pytest-cov + moto |

---

## 1. Framework Migration

### Replace
- `unittest` + deprecated `nose`

### With
- `pytest>=8.0.0` - Modern test framework
- `pytest-cov>=4.1.0` - Coverage integration
- `pytest-mock>=3.12.0` - Enhanced mocking
- `moto>=5.0.0` - AWS service mocking
- `freezegun>=1.4.0` - Time mocking for delays

### Why pytest
- Actively maintained
- Better fixtures and parametrization
- Built-in mocking improvements
- Coverage integration
- AWS Lambda Powertools compatible

---

## 2. Required Dependencies

### File: `source/lambda/shared/requirements-dev.txt`

```
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
moto>=5.0.0
freezegun>=1.4.0
boto3>=1.34.0
```

---

## 3. New Test Files Required

### 3.1 Lambda Handler Tests (Priority 1)

**File:** `source/lambda/tests/test_alb_alarm_lambda_handler.py`

```python
import pytest
from unittest.mock import MagicMock, patch
import json

@pytest.fixture
def lambda_context():
    context = MagicMock()
    context.function_name = "ALBAlarmLambda"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:ALBAlarmLambda"
    return context

@pytest.fixture
def eventbridge_alarm_event():
    return {
        'id': 'test-event-id',
        'detail-type': 'CloudWatch Alarm State Change',
        'resources': ['arn:aws:cloudwatch:us-east-1:123456789012:alarm:ALBTargetGroupAlarm'],
        'detail': {
            'alarmName': 'ALBTargetGroupAlarm',
            'state': {'value': 'ALARM'},
            'configuration': {
                'metrics': [{
                    'metricStat': {
                        'metric': {
                            'dimensions': {
                                'TargetGroup': 'targetgroup/AppServerATG/090a4ba28ada9d48'
                            }
                        }
                    }
                }]
            }
        },
        'account': '123456789012',
        'region': 'us-east-1'
    }

def test_lambda_handler_alarm_state(eventbridge_alarm_event, lambda_context):
    """Test handler processes ALARM state correctly"""
    pass

def test_lambda_handler_ok_state(eventbridge_alarm_event, lambda_context):
    """Test handler processes OK state correctly"""
    pass

def test_lambda_handler_invalid_event_type(lambda_context):
    """Test handler rejects invalid event types"""
    pass

def test_lambda_handler_missing_environment_vars(lambda_context):
    """Test handler fails gracefully with missing env vars"""
    pass
```

**File:** `source/lambda/tests/test_alb_alarm_check_lambda_handler.py`

```python
def test_sqs_message_handler_shed_action():
    """Test SQS message triggers shed action"""
    pass

def test_sqs_message_handler_restore_action():
    """Test SQS message triggers restore action"""
    pass

def test_sqs_message_handler_empty_records():
    """Test handler handles empty SQS records"""
    pass

def test_sqs_message_handler_malformed_message():
    """Test handler handles malformed JSON"""
    pass
```

### 3.2 Message Serialization Tests (Priority 3)

**File:** `source/lambda/shared/elb_load_monitor/tests/test_alb_alarm_messages.py`

```python
def test_alarm_status_message_to_json():
    """Test message serialization"""
    pass

def test_alarm_status_message_from_json():
    """Test message deserialization"""
    pass

def test_alarm_status_message_roundtrip():
    """Test serialize -> deserialize preserves data"""
    pass

def test_alarm_event_creation():
    """Test ALBAlarmEvent initialization"""
    pass
```

### 3.3 Error Handling Tests (Priority 2)

**File:** `source/lambda/shared/elb_load_monitor/tests/test_error_handling.py`

```python
def test_handle_alarm_boto3_client_error():
    """Test handling of boto3 ClientError"""
    pass

def test_handle_alarm_listener_not_found():
    """Test handling of missing listener"""
    pass

def test_handle_alarm_invalid_target_group():
    """Test handling of invalid target group ARN"""
    pass

def test_send_sqs_notification_failure():
    """Test SQS send failure handling"""
    pass

def test_handle_alarm_status_message_no_alarm():
    """Test handling when alarm doesn't exist"""
    pass
```

### 3.4 Edge Case Tests (Priority 4)

**Expand:** `source/lambda/shared/elb_load_monitor/tests/test_elb_listener_rule.py`

```python
def test_shed_at_max_limit():
    """Test shedding when at maxElbShedPercent"""
    pass

def test_shed_exceeds_max_limit():
    """Test shedding caps at maxElbShedPercent"""
    pass

def test_restore_with_zero_weight():
    """Test restore when STG has 0 weight"""
    pass

def test_shed_with_three_target_groups():
    """Test shed distributes across 3+ target groups"""
    pass

def test_restore_with_remainder():
    """Test restore handles remainder correctly"""
    pass

def test_shed_negative_weight_prevention():
    """Test weights never go negative"""
    pass
```

### 3.5 Integration Tests (Priority 6)

**File:** `source/lambda/tests/integration/test_end_to_end.py`

```python
from moto import mock_elbv2, mock_sqs, mock_cloudwatch

@mock_elbv2
@mock_sqs
@mock_cloudwatch
def test_full_shed_restore_cycle():
    """Test complete shed -> restore cycle with mocked AWS services"""
    pass

@mock_elbv2
def test_multiple_shed_increments():
    """Test multiple shed actions reach max limit"""
    pass

@mock_elbv2
def test_restore_to_steady_state():
    """Test restore returns to 100% PTG"""
    pass
```

### 3.6 CDK Tests (Priority 5)

**File:** `cdk/tests/test_alb_monitor_stack.py`

```python
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

def test_stack_creates_lambda_functions():
    """Test stack creates both Lambda functions"""
    pass

def test_stack_creates_sqs_queue():
    """Test stack creates SQS queue"""
    pass

def test_stack_creates_cloudwatch_alarm():
    """Test stack creates CloudWatch alarm"""
    pass

def test_stack_creates_eventbridge_rule():
    """Test stack creates EventBridge rule"""
    pass

def test_lambda_has_correct_environment_vars():
    """Test Lambda environment variables are set"""
    pass

def test_iam_roles_have_required_permissions():
    """Test IAM roles have minimum required permissions"""
    pass

def test_sqs_has_dead_letter_queue():
    """Test SQS has DLQ configured (after adding DLQ)"""
    pass
```

---

## 4. Test Configuration

### File: `pytest.ini`

```ini
[pytest]
testpaths = 
    source/lambda/tests 
    source/lambda/shared/elb_load_monitor/tests 
    cdk/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --cov=source/lambda/shared/elb_load_monitor
    --cov=source/lambda
    --cov=cdk/cdk
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
```

### File: `.coveragerc`

```ini
[run]
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## 5. Test Execution

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest source/lambda/tests/test_alb_alarm_lambda_handler.py

# Run with verbose output
pytest -v

# Generate HTML coverage report
pytest --cov-report=html
open htmlcov/index.html

# Run only unit tests (exclude integration)
pytest --ignore=source/lambda/tests/integration
```

---

## 6. Coverage Goals

| Component | Current | Target |
|-----------|---------|--------|
| `elb_listener_rule.py` | ~60% | 90% |
| `alb_listener_rules_handler.py` | ~50% | 85% |
| `alb_alarm_messages.py` | 0% | 80% |
| Lambda handlers | 0% | 75% |
| CDK stack | 0% | 70% |
| **Overall** | **~30%** | **80%** |

---

## 7. Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| 1 | Lambda handler tests | 4h | High - critical path, 0% coverage |
| 2 | Error handling tests | 2h | High - production resilience |
| 3 | Message serialization tests | 1h | Medium - data integrity |
| 4 | Edge case tests | 2h | Medium - algorithm correctness |
| 5 | CDK tests | 3h | Medium - infrastructure validation |
| 6 | Integration tests | 4h | Low - end-to-end validation |

**Total Estimated Effort:** 16 hours

---

## 8. Migration Steps

1. Add `requirements-dev.txt` with pytest dependencies
2. Create `pytest.ini` and `.coveragerc`
3. Remove `nose` from `setup.py`
4. Convert existing tests to pytest style (minimal changes needed)
5. Add new test files in priority order
6. Run coverage and iterate until 80%+
