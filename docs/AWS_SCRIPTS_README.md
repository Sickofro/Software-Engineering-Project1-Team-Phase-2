# AWS helper scripts

This folder contains two helpful scripts you can run locally to create and cleanup AWS resources used by this project.

Files
- `scripts/aws_create_resources.sh` — Creates the S3 bucket, lifecycle policy, IAM role (with managed policies), packages and deploys the Lambda function (or updates it).
- `scripts/aws_cleanup.sh` — Deletes the S3 bucket (and contents), DynamoDB table, Lambda function, and IAM role.

How to use
1. Inspect both scripts and ensure they match the resource names you want.
2. Ensure `aws configure` is set with credentials for an account that has permissions to create these resources.
3. Run create script:

```bash
chmod +x scripts/aws_create_resources.sh
./scripts/aws_create_resources.sh
```

4. When you're done, teardown with:

```bash
chmod +x scripts/aws_cleanup.sh
./scripts/aws_cleanup.sh
```

Security notes
- Do NOT store AWS credentials in the repo. Use `aws configure` or GitHub Actions Secrets.
- The create script attaches AWS-managed policies for convenience. For production, replace with least-privilege policies limited to the specific resources.

Cost-safety notes
- The create script applies a 1-day lifecycle rule to the S3 bucket to reduce storage costs for test artifacts.
- Use the cleanup script to remove resources when you finish testing.
