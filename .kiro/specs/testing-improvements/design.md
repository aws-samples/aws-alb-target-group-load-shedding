# Testing Improvements - Design Document

## 1. Overview

This design document outlines the approach for improving test coverage from ~30% to 80%+ by migrating to pytest and adding comprehensive tests.

## 2. Current State

| Metric | Value |
|--------|-------|
| Test Files | 2 |
| Test Methods | 12 |
| Estimated Coverage | ~30% |
| Framework | unittest + nose (deprecated) |

## 3. Target State

| Metric | Value |
|--------|-------|
| Test Files | 8+ |
| Test Methods | 40+ |
| Target Coverage | 80%+ |
| Framework | pytest + pytest-cov + moto |

## 4. Framework Migration

### 4.1 Replace

- `unittest` + deprecated `nose`

### 4.2 With

- `pytest>=8.0.0` - Modern test framework
- `pytest-cov>=4.1.0` - Coverage integration
- `pytest-mock>=3.12.0` - Enhanced mocking
- `moto>=5.0.0` - AWS service mocking
- `freezegun>=1.4.0` - Time mocking for delays

### 4.3 Why pytest

- Actively maintained
- Better fixtures and parametrization
- Built-in mocking improvements
- Coverage integration
- AWS Lambda Powertools compatible

## 5. Test File Structure

```
source/lambda/
├── tests/
│   ├── __init__.py
│   ├── test_alb_alarm_lambda_handler.py      # NEW
│   ├── test_alb_alarm_check_lambda_handler.py # NEW
│   └── integration/
│       ├── __init__.py
│       └── test_end_to_end.py                 # NEW
└── shared/
    └── elb_load_monitor/
        └── tests/
            ├── test_alb_listener_rules_handler.py  # EXISTS
            ├── test_elb_listener_rule.py           # EXISTS
            ├── test_alb_alarm_messages.py          # NEW
            └── test_error_handling.py              # NEW

cdk/
└── tests/
    ├── __init__.py
    └── test_alb_monitor_stack.py              # NEW
```

## 6. Dependencies

### 6.1 File: `source/lambda/shared/requirements-dev.txt`

```
pytest>=8.0.0
pytest-cov>=4.1.0
pytest-mock>=3.12.0
moto>=5.0.0
freezegun>=1.4.0
boto3>=1.34.0
```

## 7. Test Configuration

### 7.1 File: `pytest.ini`

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

### 7.2 File: `.coveragerc`

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

## 8. Test Execution

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

## 9. Coverage Goals

| Component | Current | Target |
|-----------|---------|--------|
| `elb_listener_rule.py` | ~60% | 90% |
| `alb_listener_rules_handler.py` | ~50% | 85% |
| `alb_alarm_messages.py` | 0% | 80% |
| Lambda handlers | 0% | 75% |
| CDK stack | 0% | 70% |
| **Overall** | **~30%** | **80%** |

## 10. Implementation Priority

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| 1 | Lambda handler tests | 4h | High - critical path, 0% coverage |
| 2 | Error handling tests | 2h | High - production resilience |
| 3 | Message serialization tests | 1h | Medium - data integrity |
| 4 | Edge case tests | 2h | Medium - algorithm correctness |
| 5 | CDK tests | 3h | Medium - infrastructure validation |
| 6 | Integration tests | 4h | Low - end-to-end validation |

**Total Estimated Effort:** 16 hours

## 11. Migration Steps

1. Add `requirements-dev.txt` with pytest dependencies
2. Create `pytest.ini` and `.coveragerc`
3. Remove `nose` from `setup.py`
4. Convert existing tests to pytest style (minimal changes needed)
5. Add new test files in priority order
6. Run coverage and iterate until 80%+

## 12. Test Templates

See `testing-improvements.md` in the original spec for detailed test templates and fixtures.
