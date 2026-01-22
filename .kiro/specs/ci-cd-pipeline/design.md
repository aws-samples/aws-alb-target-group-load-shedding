# CI/CD Pipeline - Design Document

## 1. Workflow Structure

```
.github/
└── workflows/
    ├── test.yml        # Run tests on PR
    ├── security.yml    # Security scanning
    ├── deploy.yml      # CDK deployment
    └── lint.yml        # Code quality
```

## 2. Test Workflow

### 2.1 test.yml

```yaml
name: Test

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          pip install -r source/lambda/shared/requirements.txt
          pip install -r source/lambda/shared/requirements-dev.txt
          
      - name: Run tests
        run: |
          pytest --cov=source/lambda/shared/elb_load_monitor \
                 --cov=source/lambda \
                 --cov-report=xml \
                 --cov-fail-under=80
                 
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage.xml
```

## 3. Security Workflow

### 3.1 security.yml

```yaml
name: Security

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install pip-audit
        run: pip install pip-audit
        
      - name: Scan dependencies
        run: pip-audit -r source/lambda/shared/requirements.txt
        
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Gitleaks scan
        uses: gitleaks/gitleaks-action@v2
        
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run bandit
        run: |
          pip install bandit
          bandit -r source/lambda -ll
```

## 4. Deploy Workflow

### 4.1 deploy.yml

```yaml
name: Deploy

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  id-token: write
  contents: read

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
          
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install CDK
        run: npm install -g aws-cdk
        
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: pip install -r cdk/requirements.txt
        
      - name: CDK Synth
        run: cdk synth
        working-directory: cdk
        
      - name: CDK Diff
        run: cdk diff
        working-directory: cdk
        
      - name: CDK Deploy
        run: cdk deploy --require-approval never
        working-directory: cdk

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      # Same as staging with production role
```

## 5. Lint Workflow

### 5.1 lint.yml

```yaml
name: Lint

on:
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          
      - name: Install tools
        run: pip install black ruff mypy
        
      - name: Check formatting
        run: black --check source/ cdk/
        
      - name: Run linter
        run: ruff check source/ cdk/
        
      - name: Type check
        run: mypy source/lambda/shared/elb_load_monitor
```

## 6. AWS OIDC Setup

### 6.1 IAM Role for GitHub Actions

```python
# In CDK or CloudFormation
iam.Role(
    self, "GitHubActionsRole",
    assumed_by=iam.FederatedPrincipal(
        f"arn:aws:iam::{account}:oidc-provider/token.actions.githubusercontent.com",
        conditions={
            "StringEquals": {
                "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
            },
            "StringLike": {
                "token.actions.githubusercontent.com:sub": "repo:org/repo:*"
            }
        },
        assume_role_action="sts:AssumeRoleWithWebIdentity"
    )
)
```

## 7. Estimated Effort

| Task | Effort |
|------|--------|
| test.yml | 0.5h |
| security.yml | 0.5h |
| deploy.yml | 1h |
| lint.yml | 0.25h |
| AWS OIDC setup | 0.5h |
| **Total** | **2-3h** |
