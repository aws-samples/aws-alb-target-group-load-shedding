---
inclusion: always
---

# Testing Policy

## Mandatory Requirements

### Test Coverage Requirements

**Every code modification MUST include adequate unit test coverage:**

1. **New Features** - Minimum 80% line coverage for new code
2. **Bug Fixes** - Test case reproducing the bug + fix verification
3. **Refactoring** - Maintain or improve existing coverage
4. **Lambda Handlers** - Test all code paths including error handling
5. **CDK Stacks** - Snapshot tests for infrastructure changes

### Pre-Commit Verification

**All commits MUST pass the full unit test suite:**

1. **Automated Execution** - Tests run automatically before commit via pre-commit hook
2. **Zero Failures** - Commit blocked if any test fails
3. **Coverage Check** - Commit blocked if coverage drops below 80%
4. **Fast Feedback** - Test suite must complete in <60 seconds

### Test Suite Execution

```bash
# Run before every commit (automated via hook)
pytest --cov=source/lambda/shared/elb_load_monitor \
       --cov=source/lambda \
       --cov=cdk/cdk \
       --cov-fail-under=80 \
       --maxfail=1 \
       -q
```

### Coverage Targets

| Component | Minimum Coverage |
|-----------|------------------|
| Lambda Handlers | 75% |
| Core Business Logic | 85% |
| CDK Infrastructure | 70% |
| Overall Project | 80% |

### Exemptions

Only these scenarios allow commits without new tests:
- Documentation-only changes
- Configuration file updates (non-code)
- Test file modifications
- README/markdown updates

### Enforcement

Pre-commit hook automatically:
1. Runs full test suite
2. Checks coverage thresholds
3. Blocks commit on failure
4. Provides clear error messages

**No bypassing allowed** - Use `--no-verify` only for emergency hotfixes, which require immediate follow-up PR with tests.
