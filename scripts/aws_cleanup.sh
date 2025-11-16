#!/usr/bin/env bash
# Deletes resources created by the setup script. Review before running.
set -euo pipefail

BUCKET="ml-evaluator-artifacts"
TABLE="ml-model-evaluator"
FUNC="ml-model-evaluator-staging"
ROLE="ml-evaluator-lambda-role"

echo "Deleting S3 bucket contents and bucket: $BUCKET"
aws s3 rb s3://"$BUCKET" --force || true

echo "Deleting DynamoDB table: $TABLE"
aws dynamodb delete-table --table-name "$TABLE" || true

echo "Deleting Lambda function: $FUNC"
aws lambda delete-function --function-name "$FUNC" || true

# Detaching policies and deleting role: $ROLE
POLICIES=(
  arn:aws:iam::aws:policy/AmazonS3FullAccess
  arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
  arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
)
for p in "${POLICIES[@]}"; do
  aws iam detach-role-policy --role-name "$ROLE" --policy-arn "$p" || true
done
aws iam delete-role --role-name "$ROLE" || true

echo "Cleanup complete."