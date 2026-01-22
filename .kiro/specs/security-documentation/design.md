# Security Documentation - Design Document

## 1. SECURITY.md Template

```markdown
# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **GitHub Security Advisories** (Preferred)
   - Go to the Security tab of this repository
   - Click "Report a vulnerability"
   - Provide detailed information

2. **Email**
   - Send details to: security@example.com
   - Include "SECURITY" in subject line

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

### Safe Harbor

We will not pursue legal action against security researchers who:
- Act in good faith
- Avoid privacy violations
- Do not disrupt services
- Report findings responsibly

## Security Updates

Security updates are released as patch versions. Subscribe to releases to stay informed.
```

## 2. Threat Model

### 2.1 System Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                     AWS Account                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ CloudWatch  │  │ EventBridge │  │      Lambda         │  │
│  │   Alarm     │──│    Rule     │──│  (Execution Role)   │  │
│  └─────────────┘  └─────────────┘  └──────────┬──────────┘  │
│                                                │             │
│  ┌─────────────┐                   ┌──────────▼──────────┐  │
│  │    SQS      │◀──────────────────│   ALB Listener      │  │
│  │   Queue     │                   │      Rules          │  │
│  └─────────────┘                   └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Trust Zones

| Zone | Components | Trust Level |
|------|------------|-------------|
| AWS Control Plane | CloudWatch, EventBridge | High |
| Compute | Lambda functions | Medium |
| Data | SQS messages | Medium |
| Network | ALB, Target Groups | High |

### 2.3 STRIDE Analysis

| Threat | Category | Mitigation |
|--------|----------|------------|
| Unauthorized rule modification | Tampering | IAM least privilege |
| Message injection | Spoofing | SQS access policy |
| Denial of service | DoS | Lambda concurrency limits |
| Information disclosure | Info Disclosure | Encryption at rest |
| Privilege escalation | Elevation | Scoped IAM roles |
| Audit log tampering | Repudiation | CloudTrail logging |

### 2.4 Residual Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Compromised AWS credentials | Low | High | MFA, credential rotation |
| Lambda code injection | Very Low | High | Code review, SAST |
| SQS message tampering | Low | Medium | Message validation |

## 3. Security Architecture

### 3.1 IAM Permissions

```
Lambda Execution Role
├── elasticloadbalancing:DescribeRules
├── elasticloadbalancing:ModifyRule
├── elasticloadbalancing:ModifyListener
├── sqs:SendMessage (scoped to queue)
├── sqs:ReceiveMessage (scoped to queue)
├── cloudwatch:DescribeAlarms
└── logs:* (scoped to log group)
```

### 3.2 Encryption

| Data | At Rest | In Transit |
|------|---------|------------|
| SQS Messages | SSE-SQS | TLS 1.2+ |
| Lambda Env Vars | AWS KMS | N/A |
| CloudWatch Logs | SSE-S3 | TLS 1.2+ |

### 3.3 Network Security

- Lambda runs in AWS-managed VPC (no customer VPC)
- All API calls over HTTPS
- No inbound network access required

## 4. SBOM Generation

### 4.1 Using cyclonedx-bom

```bash
pip install cyclonedx-bom
cyclonedx-py requirements \
  -i source/lambda/shared/requirements.txt \
  -o sbom.json \
  --format json
```

### 4.2 CI Integration

```yaml
- name: Generate SBOM
  run: |
    pip install cyclonedx-bom
    cyclonedx-py requirements -i requirements.txt -o sbom.json
    
- name: Upload SBOM
  uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom.json
```

## 5. Estimated Effort

| Task | Effort |
|------|--------|
| SECURITY.md | 0.5h |
| Threat model | 1h |
| Security architecture | 0.5h |
| SBOM setup | 0.25h |
| **Total** | **2h** |
