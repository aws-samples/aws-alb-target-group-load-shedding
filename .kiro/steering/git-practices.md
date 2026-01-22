# Git Best Practices

## Commit Message Format

Use conventional commits:

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation only
- `refactor` - Code change that neither fixes a bug nor adds a feature
- `test` - Adding or updating tests
- `chore` - Build process, dependencies, tooling
- `ci` - CI/CD changes

**Scopes (this project):**
- `lambda` - Lambda handler code
- `layer` - elb_load_monitor shared layer
- `cdk` - CDK infrastructure
- `spec` - Kiro spec files
- `build` - Build scripts

**Examples:**
```
feat(layer): add multi-target group support to shed algorithm
fix(lambda): handle missing environment variables gracefully
docs(spec): add testing improvements to tasks.md
chore(cdk): upgrade to CDK v2
test(layer): add edge case tests for restore logic
```

## Branch Naming

```
<type>/<short-description>
```

**Examples:**
- `feat/cdk-v2-migration`
- `fix/sqs-dlq-handling`
- `test/lambda-handler-coverage`
- `docs/update-readme`

## Commit Guidelines

- **Atomic commits** - One logical change per commit
- **Commit early, commit often** - Don't batch unrelated changes
- **Working state** - Each commit should leave the codebase in a working state
- **Test before commit** - Run tests before committing code changes

## When to Commit

Commit after:
- Completing a single task from tasks.md
- Adding/modifying a test file
- Updating documentation
- Fixing a bug
- Adding a new feature component

Don't batch:
- Multiple unrelated file changes
- Code changes with unrelated doc updates
- Multiple bug fixes in one commit

## Pull Request Guidelines

- Reference related spec tasks in PR description
- Include test coverage for new code
- Update documentation if behavior changes
- Keep PRs focused on single concern
