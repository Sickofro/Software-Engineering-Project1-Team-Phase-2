#!/usr/bin/env bash
# Creates S3 bucket, lifecycle, IAM role, attaches policies, and creates (or updates) a Lambda function
# WARNING: This runs real AWS commands. Review before running. Use with care (costs may apply).

set -euo pipefail

BUCKET="ml-evaluator-artifacts"
TABLE="ml-model-evaluator"
ROLE_NAME="ml-evaluator-lambda-role"
FUNC_NAME="ml-model-evaluator-staging"
REGION="us-east-1"

# Get ACCOUNT_ID if not provided
if [ -z "${AWS_ACCOUNT_ID:-}" ]; then
  echo "Detecting AWS account ID via sts..."
  AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
fi

echo "Using AWS account: $AWS_ACCOUNT_ID"

echo "1/6: Create S3 bucket (if it doesn't exist)..."
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Bucket $BUCKET already exists"
else
  if [ "$REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint=$REGION
  fi
  echo "Bucket created: $BUCKET"
fi

# Apply lifecycle rule to auto-expire objects after 1 day (safe default)
cat > /tmp/lifecycle.json <<'EOF'
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
EOF

echo "Applying lifecycle rule to $BUCKET"
aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET" \
  --lifecycle-configuration file:///tmp/lifecycle.json || true


echo "2/6: Create (or ensure) IAM role and attach policies"
cat > /tmp/trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "Role $ROLE_NAME already exists"
else
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file:///tmp/trust-policy.json
  echo "Created role $ROLE_NAME"
fi

# Attach minimal set of managed policies (modify later for least-privilege)
POLICIES=(
  arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
  arn:aws:iam::aws:policy/AmazonS3FullAccess
  arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
)
for p in "${POLICIES[@]}"; do
  echo "Attaching policy $p to $ROLE_NAME"
  aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "$p" || true
done

# Allow role to propagate in IAM (fixes "cannot be assumed by Lambda" error)
echo "Waiting 5 seconds for IAM role to propagate..."
sleep 5


echo "3/6: Prepare Lambda deployment package (zips current src/aws folder)"
ZIPFILE="/tmp/ml_deploy_package.zip"
rm -f "$ZIPFILE"
if [ -d "src/aws" ]; then
  (cd src && zip -r "$ZIPFILE" aws) >/dev/null
else
  # create a minimal handler if src/aws is absent
  mkdir -p /tmp/ml_lambda_src
  cat > /tmp/ml_lambda_src/lambda_handler.py <<'PY'
def lambda_handler(event, context):
    return {"statusCode":200, "body":"noop"}
PY
  (cd /tmp && zip -r "$ZIPFILE" ml_lambda_src) >/dev/null
fi


echo "4/6: Create or update Lambda function"
ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
if aws lambda get-function --function-name "$FUNC_NAME" >/dev/null 2>&1; then
  echo "Function exists; updating code and configuration"
  aws lambda update-function-code --function-name "$FUNC_NAME" --zip-file fileb://"$ZIPFILE"
  aws lambda update-function-configuration --function-name "$FUNC_NAME" \
    --environment Variables={DYNAMODB_TABLE=$TABLE,S3_BUCKET=$BUCKET} || true
else
  aws lambda create-function \
    --function-name "$FUNC_NAME" \
    --runtime python3.11 \
    --role "$ROLE_ARN" \
    --handler src.aws.lambda_handler.lambda_handler \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{DYNAMODB_TABLE=$TABLE,S3_BUCKET=$BUCKET}" \
    --zip-file fileb://"$ZIPFILE" \
    --region "$REGION"
fi


echo "5/6: Verification (short)"
aws s3api head-bucket --bucket "$BUCKET" && echo "S3 OK"
aws dynamodb describe-table --table-name "$TABLE" --query 'Table.TableStatus' && echo "DynamoDB OK"
aws lambda get-function --function-name "$FUNC_NAME" --query 'Configuration.FunctionName' && echo "Lambda OK"


echo "6/6: Done. If you want least-privilege policies, I can help craft them next."

echo "If you want to cleanup later, run: scripts/aws_cleanup.sh"
