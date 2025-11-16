# AWS Deployment Guide

This document describes how to deploy the ML Model Evaluator to AWS using GitHub Actions CI/CD.

## Architecture Overview

The deployment uses the following AWS components:

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub (CI/CD)                         │
│                    (GitHub Actions)                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ Lint/Type/Test (Ubuntu runner)
                      ├─→ Build Distribution
                      │
                      └─→ Deploy to AWS
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    API Gateway      Lambda Function      CloudWatch
    (REST API)       (Staging)            (Logs & Metrics)
        │                 │                 │
        │                 ├─→ DynamoDB      │
        │                 │   (Metadata)    │
        │                 │                 │
        │                 └─→ S3            │
        │                     (Artifacts)   │
        │                                   │
        └───────────────────────────────────┘
```

## Prerequisites

### Local Setup
1. **AWS Account** with appropriate IAM permissions
2. **GitHub Repository** with Secrets configured
3. **AWS CLI** installed locally (optional but recommended)
4. **Python 3.11+** with boto3 and botocore

### AWS Resources Required
- **IAM Role** for Lambda execution
- **DynamoDB Table** named `ml-model-evaluator`
- **S3 Bucket** named `ml-evaluator-artifacts`
- **CloudWatch Log Group** for monitoring
- **API Gateway** with Lambda integration (optional for API)

## GitHub Secrets Configuration

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_ACCESS_KEY_ID       - Your AWS Access Key
AWS_SECRET_ACCESS_KEY   - Your AWS Secret Key
PYPI_API_TOKEN          - (Optional) For PyPI publishing
STAGING_API_ENDPOINT    - Your staging API Gateway URL
```

## Setting Up AWS Resources

### 1. Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name ml-model-evaluator \
  --attribute-definitions \
    AttributeName=id,AttributeType=S \
  --key-schema \
    AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 2. Create S3 Bucket

```bash
aws s3api create-bucket \
  --bucket ml-evaluator-artifacts \
  --region us-east-1
```

Enable versioning (for audit trail):
```bash
aws s3api put-bucket-versioning \
  --bucket ml-evaluator-artifacts \
  --versioning-configuration Status=Enabled
```

### 3. Create IAM Role for Lambda

```bash
# Create trust policy JSON
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name ml-evaluator-lambda-role \
  --assume-role-policy-document file://trust-policy.json
```

Attach policies:
```bash
# DynamoDB access
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

# S3 access
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

# CloudWatch Logs
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

# CloudWatch Metrics
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchMetricsFullAccess
```

### 4. Create Lambda Function

```bash
# First, run the build locally to create the Lambda package
# (This is done automatically by GitHub Actions)

# Then create the function (if not using CloudFormation):
aws lambda create-function \
  --function-name ml-model-evaluator-staging \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/ml-evaluator-lambda-role \
  --handler src.aws.lambda_handler.lambda_handler \
  --zip-file fileb://ml-evaluator-lambda.zip \
  --timeout 300 \
  --memory-size 512 \
  --environment Variables="{DYNAMODB_TABLE=ml-model-evaluator,S3_BUCKET=ml-evaluator-artifacts}" \
  --region us-east-1
```

### 5. Create API Gateway

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
  --name ml-model-evaluator \
  --description "ML Model Evaluator API" \
  --query 'id' \
  --output text)

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' \
  --output text)

# Create resource
RESOURCE_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "{proxy+}" \
  --query 'id' \
  --output text)

# Create ANY method (handles all HTTP methods)
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --authorization-type NONE

# Integrate with Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method ANY \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:ml-model-evaluator-staging/invocations

# Deploy API
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name staging

echo "API Gateway ID: $API_ID"
```

## GitHub Actions Workflow

The workflow (`.github/workflows/cd.yml`) performs:

1. **Lint Stage** - Checks code quality with flake8
2. **Type Check** - Validates types with mypy
3. **Test Stage** - Runs pytest with coverage (≥60% target)
4. **Build Stage** - Creates Python distribution package
5. **Publish Stage** - Uploads to PyPI (if PYPI_API_TOKEN set)
6. **Deploy to AWS** - Deploys Lambda function to staging environment
7. **Smoke Tests** - Runs health check against staging API
8. **Metrics** - Posts deployment status to CloudWatch

## Local Testing

Test the deployment locally before pushing:

```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Test DynamoDB operations
python -c "
from src.aws.dynamodb_service import DynamoDBService
db = DynamoDBService()
item = db.create_item('test-model', 'huggingface', 'MIT', {})
print('Created:', item)
"

# Test S3 operations
python -c "
from src.aws.s3_service import S3Service
s3 = S3Service()
result = s3.upload_bytes(b'test data', 'test/data.txt')
print('Uploaded:', result)
"

# Test Lambda handler
python -c "
from src.aws.lambda_handler import lambda_handler
event = {'httpMethod': 'GET', 'path': '/health'}
context = None
response = lambda_handler(event, context)
print('Response:', response)
"
```

## Deployment Workflow

### First-Time Setup
1. Create AWS resources (DynamoDB, S3, Lambda, API Gateway)
2. Add GitHub Secrets
3. Push to `main` branch
4. GitHub Actions automatically deploys to staging
5. Check CloudWatch logs for errors

### Subsequent Deployments
1. Make code changes on a feature branch
2. Create Pull Request
3. GitHub Actions runs tests (must pass)
4. Merge to `main`
5. GitHub Actions automatically deploys to staging

### Manual Deployment (if needed)
```bash
# Build and package locally
mkdir -p lambda_package
cp -r src lambda_package/
cp -r main.py lambda_package/
cp requirements.txt lambda_package/

cd lambda_package
pip install -r requirements.txt -t . --upgrade
zip -r ../ml-evaluator-lambda.zip .

# Upload to AWS
aws lambda update-function-code \
  --function-name ml-model-evaluator-staging \
  --zip-file fileb://../ml-evaluator-lambda.zip
```

## Monitoring & Observability

### CloudWatch Logs
View logs:
```bash
aws logs tail /aws/lambda/ml-model-evaluator-staging --follow
```

### CloudWatch Metrics
View deployment metrics:
```bash
aws cloudwatch get-metric-statistics \
  --namespace ML-Evaluator \
  --metric-name DeploymentStatus \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Health Check Endpoint
```bash
curl https://YOUR_API_GATEWAY_URL/health
```

## Troubleshooting

### Lambda Function Not Updating
- Check IAM permissions for Lambda update
- Verify S3 bucket exists and is accessible
- Check CloudWatch logs: `aws logs tail /aws/lambda/ml-model-evaluator-staging`

### DynamoDB Connection Issues
- Verify table exists: `aws dynamodb describe-table --table-name ml-model-evaluator`
- Check IAM role has DynamoDB permissions
- Ensure Lambda execution role is attached to function

### S3 Upload Failures
- Verify bucket exists: `aws s3api head-bucket --bucket ml-evaluator-artifacts`
- Check S3 bucket policy allows Lambda access
- Verify versioning is enabled (for audit trail)

### API Gateway Not Responding
- Check API Gateway ID: `aws apigateway get-rest-apis`
- Verify Lambda integration: `aws apigateway get-integration`
- Check Lambda permissions: `aws lambda get-policy --function-name ml-model-evaluator-staging`

## Cost Estimation

**Monthly costs (rough estimate):**
- Lambda: ~$0.20 (1M free requests/month, 400K seconds free/month)
- DynamoDB: ~$0-5 (on-demand pricing, free tier includes 25 read/write units)
- S3: ~$1-10 (depends on storage volume)
- CloudWatch: ~$0.50 (logs retention)
- API Gateway: ~$3.50 (1M API calls/month)

**Total: ~$5-20/month for low-traffic staging environment**

## Next Steps

1. ✅ GitHub Actions CI/CD pipeline configured
2. ✅ Lambda deployment automation working
3. ✅ DynamoDB metadata storage ready
4. ✅ S3 artifact storage ready
5. ⏳ Create CloudFormation template for infrastructure as code
6. ⏳ Add performance benchmarking tests
7. ⏳ Set up production deployment stage
8. ⏳ Configure auto-scaling policies

## References

- [AWS Lambda Handler Reference](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [DynamoDB Python Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GettingStarted.Python.html)
- [S3 Python Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingPythonSDK.html)
- [GitHub Actions AWS Documentation](https://github.com/aws-actions/configure-aws-credentials)
