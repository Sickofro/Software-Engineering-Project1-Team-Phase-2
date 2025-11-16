# Cost-safety & Local Testing (recommended)

This document contains low-cost practices and quick commands so you don't accidentally spend your AWS credits.

## 1) Local testing / emulation — no AWS charges

- LocalStack (Docker) — full-stack emulation (S3, DynamoDB, Lambda, etc.)

```bash
# Start LocalStack (requires Docker)
docker run --rm -it -p 4566:4566 -p 4571:4571 localstack/localstack
# Example: point AWS CLI at LocalStack endpoint
aws --endpoint-url=http://localhost:4566 s3 ls
```

- moto (Python) — lightweight mocking for unit tests

```bash
pip install moto
# In pytest use decorators like @mock_s3, @mock_dynamodb2
```

Use these for development and CI to avoid creating real resources.

## 2) Auto-expire test objects (S3 lifecycle)

Create a lifecycle rule to auto-delete objects after 1 day.

`lifecycle.json`:

```json
{
  "Rules": [
    {
      "ID": "AutoExpire",
      "Status": "Enabled",
      "Expiration": { "Days": 1 },
      "Prefix": ""
    }
  ]
}
```

Apply it:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket ml-evaluator-artifacts \
  --lifecycle-configuration file://lifecycle.json
```

## 3) Short-lived resources and TTL

Use DynamoDB Time To Live (TTL) if you store test items:

```bash
aws dynamodb update-time-to-live \
  --table-name ml-model-evaluator \
  --time-to-live-specification "{\"Enabled\":true,\"AttributeName\":\"ttl\"}"
```

## 4) Quick cleanup script (run when you're done)

Save the following as `aws_cleanup.sh`, review it, then run it to remove resources the checklist creates.

```bash
#!/usr/bin/env bash
set -euo pipefail

BUCKET=ml-evaluator-artifacts
TABLE=ml-model-evaluator
FUNC=ml-model-evaluator-staging
ROLE=ml-evaluator-lambda-role

echo "Deleting S3 bucket contents and bucket: $BUCKET"
aws s3 rb s3://"$BUCKET" --force || true

echo "Deleting DynamoDB table: $TABLE"
aws dynamodb delete-table --table-name "$TABLE" || true

echo "Deleting Lambda function: $FUNC"
aws lambda delete-function --function-name "$FUNC" || true

echo "Detaching policies and deleting role: $ROLE"
POLICIES=(
  arn:aws:iam::aws:policy/AmazonS3FullAccess
  arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
  arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
  arn:aws:iam::aws:policy/CloudWatchMetricsFullAccess
)
for p in "${POLICIES[@]}"; do
  aws iam detach-role-policy --role-name "$ROLE" --policy-arn "$p" || true
done
aws iam delete-role --role-name "$ROLE" || true

echo "Cleanup complete."
```

Make executable and run:

```bash
chmod +x aws_cleanup.sh
./aws_cleanup.sh
```

## 5) Billing protections & budgets (set $1–$5 alert)

Best: open **AWS Console → Billing → Budgets** and create a budget (e.g., $1 or $5) with an email alert.

Console steps are easiest because `aws budgets` CLI calls often require additional permissions.

Optional (console):
1. Billing → Budgets → Create budget → Cost budget
2. Set amount = 1 (USD) or 5, choose period = Monthly
3. Set alert threshold(s) and an email

## 6) Use least-privilege credentials or OIDC for CI

- Don't use root credentials. Create an IAM user with minimal permissions scoped to the specific S3 bucket, DynamoDB table and Lambda function.
- Even better: configure GitHub Actions OIDC trust for your AWS account so GitHub obtains short-lived credentials; no long-lived secrets required. I can help set that up.

## 7) Quick checklist for low-cost usage

- Develop locally with moto/LocalStack
- When using AWS: create minimal resources, small Lambda timeout and memory
- Use lifecycle rules and TTL for test data
- Delete resources with `aws_cleanup.sh` after testing
- Create a $1–$5 budget alert

---

If you want, I can also:
- Add a short pointer from `docs/AWS_SETUP_CHECKLIST.md` to this file,
- Generate the `aws_cleanup.sh` file in the repo for you,
- Or help set up GitHub OIDC so you don't need to store keys in GitHub Secrets.
