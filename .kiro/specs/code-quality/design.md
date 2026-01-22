# Code Quality - Design Document

## 1. Type Hints

### 1.1 Example: alb_alarm_messages.py

```python
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass

class CWAlarmState(Enum):
    OK = "OK"
    ALARM = "ALARM"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

class ALBAlarmAction(Enum):
    NONE = "NONE"
    SHED = "SHED"
    RESTORE = "RESTORE"

@dataclass
class ALBAlarmEvent:
    alarm_arn: str
    alarm_name: str
    state: CWAlarmState
    target_group_arn: str
    
    @classmethod
    def from_event(cls, event: Dict[str, Any]) -> "ALBAlarmEvent":
        ...

@dataclass
class ALBAlarmStatusMessage:
    alb_alarm_action: ALBAlarmAction
    alarm_arn: str
    alarm_name: str
    elb_listener_arn: str
    elb_shed_percent: int
    max_elb_shed_percent: int
    elb_restore_percent: int
    load_balancer_arn: str
    sqs_queue_url: str
    shed_mesg_delay_sec: int
    restore_mesg_delay_sec: int
    target_group_arn: str
    
    def to_json(self) -> str:
        ...
    
    @classmethod
    def from_json(cls, json_str: str) -> "ALBAlarmStatusMessage":
        ...
```

### 1.2 Example: elb_listener_rule.py

```python
from typing import Dict, List, Optional
import boto3

class ELBListenerRule:
    def __init__(
        self,
        rule_arn: str,
        listener_arn: str,
        is_default: bool = False
    ) -> None:
        ...
    
    def add_forward_config(
        self,
        target_group_arn: str,
        weight: int
    ) -> None:
        ...
    
    def is_sheddable(
        self,
        source_group_arn: str,
        max_shed_weight: int
    ) -> bool:
        ...
    
    def shed(
        self,
        source_group_arn: str,
        weight_to_shed: int,
        max_shed_weight: int
    ) -> None:
        ...
    
    def save(
        self,
        elbv2_client: boto3.client
    ) -> None:
        ...
```

## 2. Linting Configuration

### 2.1 pyproject.toml

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by formatter)
]

[tool.ruff.lint.isort]
known-first-party = ["elb_load_monitor"]
```

## 3. Formatting Configuration

### 3.1 pyproject.toml

```toml
[tool.black]
line-length = 100
target-version = ["py312"]
include = '\.pyi?$'
exclude = '''
/(
    \.git
    | \.venv
    | build
    | dist
    | \.eggs
)/
'''
```

## 4. Type Checking Configuration

### 4.1 pyproject.toml

```toml
[tool.mypy]
python_version = "3.12"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true

[[tool.mypy.overrides]]
module = "boto3.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "botocore.*"
ignore_missing_imports = true
```

## 5. Security Linting

### 5.1 bandit.yaml

```yaml
skips:
  - B101  # assert_used (OK in tests)
  
exclude_dirs:
  - tests
  - .venv
```

## 6. Pre-commit Configuration

### 6.1 .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [boto3-stubs]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.7
    hooks:
      - id: bandit
        args: [-c, bandit.yaml]
```

## 7. Code Fixes

### 7.1 Logger Warning

```python
# Before
logger.warn("No SQS message")

# After
logger.warning("No SQS message")
```

### 7.2 Parameterized Logging

```python
# Before
logger.info("Processing alarm: " + alarm_name)

# After
logger.info("Processing alarm: %s", alarm_name)
```

### 7.3 Module Exports

```python
# elb_load_monitor/__init__.py
from .alb_alarm_messages import (
    ALBAlarmEvent,
    ALBAlarmStatusMessage,
    CWAlarmState,
    ALBAlarmAction,
)
from .alb_listener_rules_handler import ALBListenerRulesHandler
from .elb_listener_rule import ELBListenerRule

__all__ = [
    "ALBAlarmEvent",
    "ALBAlarmStatusMessage",
    "CWAlarmState",
    "ALBAlarmAction",
    "ALBListenerRulesHandler",
    "ELBListenerRule",
]
```

## 8. Estimated Effort

| Task | Effort |
|------|--------|
| Type hints | 2-3h |
| Linting setup | 0.5h |
| Formatting | 0.5h |
| Security linting | 0.5h |
| Code fixes | 1h |
| Pre-commit hooks | 0.5h |
| **Total** | **4-6h** |
