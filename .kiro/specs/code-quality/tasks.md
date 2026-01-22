# Code Quality - Implementation Tasks

## Phase 1: Configuration

- [ ] 1. Set up tooling configuration
  - [ ] 1.1 Create/update `pyproject.toml` with tool configurations
  - [ ] 1.2 Configure ruff linting rules
  - [ ] 1.3 Configure black formatting
  - [ ] 1.4 Configure mypy type checking
  - [ ] 1.5 Create `bandit.yaml` for security linting

## Phase 2: Type Hints

- [ ] 2. Add type hints to message classes
  - [ ] 2.1 Add type hints to `CWAlarmState` enum
  - [ ] 2.2 Add type hints to `ALBAlarmAction` enum
  - [ ] 2.3 Add type hints to `ALBAlarmEvent` class
  - [ ] 2.4 Add type hints to `ALBAlarmStatusMessage` class
  - [ ] 2.5 Add type hints to serialization methods

- [ ] 3. Add type hints to ELBListenerRule
  - [ ] 3.1 Add type hints to `__init__` method
  - [ ] 3.2 Add type hints to `add_forward_config` method
  - [ ] 3.3 Add type hints to `is_sheddable` method
  - [ ] 3.4 Add type hints to `is_restorable` method
  - [ ] 3.5 Add type hints to `shed` method
  - [ ] 3.6 Add type hints to `restore` method
  - [ ] 3.7 Add type hints to `save` method

- [ ] 4. Add type hints to ALBListenerRulesHandler
  - [ ] 4.1 Add type hints to `__init__` method
  - [ ] 4.2 Add type hints to `handle_alarm` method
  - [ ] 4.3 Add type hints to `handle_alarm_status_message` method
  - [ ] 4.4 Add type hints to `shed` method
  - [ ] 4.5 Add type hints to `restore` method
  - [ ] 4.6 Add type hints to helper methods

- [ ] 5. Add type hints to Lambda handlers
  - [ ] 5.1 Add type hints to `alb_alarm_lambda_handler.py`
  - [ ] 5.2 Add type hints to `alb_alarm_check_lambda_handler.py`

## Phase 3: Code Fixes

- [ ] 6. Fix deprecation warnings
  - [ ] 6.1 Replace `logger.warn` with `logger.warning`
  - [ ] 6.2 Convert string concatenation to parameterized logging
  - [ ] 6.3 Remove unused `from re import S` import
  - [ ] 6.4 Add `__all__` exports to `__init__.py`

## Phase 4: Formatting

- [ ] 7. Apply formatting
  - [ ] 7.1 Run black on all Python files
  - [ ] 7.2 Run ruff --fix on all Python files
  - [ ] 7.3 Verify no formatting changes needed

## Phase 5: Linting

- [ ] 8. Fix linting issues
  - [ ] 8.1 Run ruff and fix all errors
  - [ ] 8.2 Run bandit and fix security issues
  - [ ] 8.3 Run mypy and fix type errors

## Phase 6: Pre-commit Hooks

- [ ] 9. Set up pre-commit
  - [ ] 9.1 Create `.pre-commit-config.yaml`
  - [ ] 9.2 Add black hook
  - [ ] 9.3 Add ruff hook
  - [ ] 9.4 Add mypy hook
  - [ ] 9.5 Add bandit hook
  - [ ] 9.6 Document pre-commit setup in README

## Phase 7: Documentation

- [ ] 10. Add docstrings
  - [ ] 10.1 Add docstrings to `ALBAlarmEvent` class
  - [ ] 10.2 Add docstrings to `ALBAlarmStatusMessage` class
  - [ ] 10.3 Add docstrings to `ELBListenerRule` class
  - [ ] 10.4 Add docstrings to `ALBListenerRulesHandler` class
  - [ ] 10.5 Add docstrings to Lambda handlers

## Summary

| Phase | Tasks | Effort | Status |
|-------|-------|--------|--------|
| 1 | 1 | 0.5h | ⬜ Not Started |
| 2 | 2-5 | 2-3h | ⬜ Not Started |
| 3 | 6 | 0.5h | ⬜ Not Started |
| 4 | 7 | 0.25h | ⬜ Not Started |
| 5 | 8 | 0.5h | ⬜ Not Started |
| 6 | 9 | 0.5h | ⬜ Not Started |
| 7 | 10 | 1h | ⬜ Not Started |

**Total Estimated Effort:** 4-6 hours
**Total Sub-tasks:** 44
