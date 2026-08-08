# AWS Deployment Context

## Goal
Small web service deployment on AWS with low fixed cost and simple operations.

## Current AWS Setup
- Region: `ap-northeast-2` (Seoul)
- EC2 name: `t4g-trial-2026-01`
- Instance type: `t4g.small`
- OS: Ubuntu Server 24.04 LTS ARM64
- Architecture: ARM64 / AWS Graviton
- EBS: `30 GiB`, `gp3`, `3000 IOPS`, `125 MiB/s`, encrypted, delete on termination enabled
- Public IPv4: enabled
- Security Group:
  - SSH `22`: current developer public IP only (`/32`)
  - HTTP/HTTPS: not opened yet
  - PostgreSQL `5432`: must NOT be exposed publicly
- Termination protection: enabled
- Stop protection: disabled
- Detailed CloudWatch monitoring: disabled
- CPU credit mode: `standard`
- Purchase option: normal On-Demand (no Spot)
- IMDS: enabled, IMDSv2 required
- Metadata hop limit: `2`
- User data: empty
- IAM instance profile: none for now

## Cost Guardrails
- AWS monthly budget: `$50`
- Budget alerts configured
- Cost Anomaly Detection configured
- T4g free trial is being used for the EC2 instance.
- Do not assume EBS, public IPv4, data transfer, or other AWS resources are covered by the T4g trial.

## Planned Architecture

```text
User
  |
  v
CloudFront
  |-- /*      -> S3 frontend
  |
  `-- /api/*  -> EC2 backend
                   |
                   `-- PostgreSQL
```

Frontend should call relative API paths such as `/api/...` to simplify HTTPS and CORS.

## Deployment Plan

### Backend
Run on EC2 with Docker Compose.

```text
EC2
  |-- backend
  `-- PostgreSQL
```

Before deployment:
1. SSH into EC2.
2. Install Docker + Docker Compose.
3. Add ~1–2 GB swap because the instance has 2 GB RAM.
4. Keep PostgreSQL private to the host/Docker network.
5. Expose only the backend/web entrypoint needed by CloudFront.

### Frontend
- Build locally or in GitHub Actions.
- Upload build artifacts to S3.
- Put CloudFront in front of S3.
- Use the CloudFront default domain initially:
  `https://<distribution>.cloudfront.net`
- Add a custom domain later if needed.

### CI/CD
Preferred end state:

```text
git push
   |
   v
GitHub Actions
   |-- frontend -> build -> S3 -> CloudFront invalidation
   `-- backend  -> deploy/restart on EC2
```

Prefer GitHub Actions OIDC for AWS authentication instead of long-lived AWS access keys.

## Domain
A custom domain is not required for initial development/testing.

Initial URL:
```text
https://<distribution>.cloudfront.net
```

Later, attach a custom domain + ACM certificate to CloudFront without changing the overall architecture.

## Important Constraints
- Do not open SSH to `0.0.0.0/0`.
- Do not expose PostgreSQL `5432` publicly.
- Avoid unnecessary paid AWS services during initial development.
- Keep CloudWatch detailed monitoring disabled unless needed.
- Keep CPU credit mode on `standard` unless sustained CPU performance is required.
- Architecture is ARM64, so Docker images/dependencies must support `linux/arm64`.
