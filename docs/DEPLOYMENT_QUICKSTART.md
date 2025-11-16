# AWS Deployment Quick Start

## Summary of Changes

I've set up a complete AWS deployment pipeline for your ML Model Evaluator project. Here's what was added:

### 📁 New Files Created

1. **`.github/workflows/cd.yml`** (Enhanced)
   - Lint, type check, test stages (pytest with coverage)
   - Build & publish to PyPI
   - **New AWS deployment stage** with:
     - Lambda function packaging and deployment
     - S3 artifact upload
     - Smoke testing against staging API
     - CloudWatch metrics posting

2. **`src/aws/dynamodb_service.py`**
   - CRUD operations for model metadata
   - Change history tracking (immutable record IDs)
   - Soft delete support
   - Filtering and listing with pagination

3. **`src/aws/s3_service.py`**
   - File and bytes upload/download
   - SHA256 hash calculation and verification
   - Metadata tagging
   - File listing with prefix filtering

4. **`src/aws/lambda_handler.py`**
   - RESTful API endpoints:
     - `GET /health` - Health check
     - `POST /models` - Create model record
     - `GET /models` - List/retrieve models
     - `PUT /models` - Update model record
     - `DELETE /models` - Soft delete
     - `POST /evaluate` - Evaluate model from URL
   - Error handling and validation
   - Integration with DynamoDB and S3

5. **`src/aws/__init__.py`**
   - Module exports for AWS services

6. **`docs/AWS_DEPLOYMENT.md`**
   - Complete deployment guide
   - Architecture diagrams
   - AWS resource setup instructions
   - Local testing examples
   - Troubleshooting guide
   - Cost estimation

7. **`requirements.txt`** (Updated)
   - Added: `boto3>=1.28.0`
   - Added: `botocore>=1.31.0`

---

## Quick Start (5 Steps)

### Step 1: Create AWS Resources
Run these commands in your terminal (requires AWS CLI):

```bash
# Create DynamoDB table
aws dynamodb create-table \
  --table-name ml-model-evaluator \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Create S3 bucket
aws s3api create-bucket \
  --bucket ml-evaluator-artifacts \
  --region us-east-1

# Enable S3 versioning (for audit trail)
aws s3api put-bucket-versioning \
  --bucket ml-evaluator-artifacts \
  --versioning-configuration Status=Enabled
```

### Step 2: Create IAM Role for Lambda
```bash
# Create trust policy
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create role
aws iam create-role \
  --role-name ml-evaluator-lambda-role \
  --assume-role-policy-document file://trust-policy.json

# Attach permissions
for policy in AmazonDynamoDBFullAccess AmazonS3FullAccess CloudWatchLogsFullAccess CloudWatchMetricsFullAccess; do
  aws iam attach-role-policy \
    --role-name ml-evaluator-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/$policy
done
```

### Step 3: Configure GitHub Secrets
In GitHub repo → Settings → Secrets and variables → Actions, add:

```
AWS_ACCESS_KEY_ID          = Your AWS Access Key
AWS_SECRET_ACCESS_KEY      = Your AWS Secret Access Key
PYPI_API_TOKEN            = (Optional) For PyPI publishing
STAGING_API_ENDPOINT      = Your staging API endpoint (after first deploy)
```

**To create AWS credentials:**
```bash
aws iam create-access-key --user-name YOUR_IAM_USER
```

### Step 4: Push to Main Branch
```bash
git add .
git commit -m "feat: Add AWS deployment with Lambda, DynamoDB, S3"
git push origin aman's-branch
# Create PR → Merge to main
```

GitHub Actions will automatically:
- ✅ Run linting and tests
- ✅ Build distribution package
- ✅ Deploy Lambda to staging
- ✅ Run smoke tests
- ✅ Post metrics to CloudWatch

### Step 5: Verify Deployment
```bash
# Check Lambda was deployed
aws lambda list-functions --region us-east-1 | grep ml-model-evaluator

# Check DynamoDB table
aws dynamodb describe-table --table-name ml-model-evaluator

# View Lambda logs
aws logs tail /aws/lambda/ml-model-evaluator-staging --follow
```

---

## Architecture

```
GitHub (code push)
    ↓
GitHub Actions CI/CD
    ├→ Lint/Type/Test
    ├→ Build
    └→ Deploy to AWS
        ├→ API Gateway (REST endpoint)
        ├→ Lambda (serverless compute)
        ├→ DynamoDB (metadata storage)
        ├→ S3 (artifact storage)
        └→ CloudWatch (monitoring)
```

---

## Key Features Added

### ✅ CRUD Operations
- **Create**: Add models with metadata, license, risk notes
- **Read**: Fetch by ID or list with filters
- **Update**: Modify fields with version tracking
- **Delete**: Soft delete (marked as inactive)

### ✅ High-Assurance Features
- **Immutable IDs**: UUID-based, can't be changed
- **Change History**: Every update tracked with timestamp, user, fields changed
- **Audit Trail**: Complete version history in DynamoDB
- **Hash Verification**: SHA256 hashes on S3 artifacts

### ✅ CI/CD Pipeline
- **Automated Tests**: pytest runs on every PR
- **Code Quality**: flake8 linting, mypy type checking
- **Automated Deployment**: Push to main → auto-deploy to staging
- **Health Checks**: Smoke tests after deployment
- **Metrics**: CloudWatch integration

### ✅ RESTful API
- `POST /models` - Create
- `GET /models?id=X` - Read
- `GET /models` - List (with filters)
- `PUT /models` - Update
- `DELETE /models` - Delete
- `POST /evaluate` - Evaluate model from URL
- `GET /health` - Health check

---

## Test the API (After Deployment)

```bash
# Health check
curl https://YOUR_API_GATEWAY_URL/health

# Create a model
curl -X POST https://YOUR_API_GATEWAY_URL/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bert-base",
    "source": "huggingface",
    "license": "Apache-2.0",
    "metadata": {"params": 110000000},
    "risk_notes": "External dependency"
  }'

# List models
curl https://YOUR_API_GATEWAY_URL/models

# Evaluate a model
curl -X POST https://YOUR_API_GATEWAY_URL/evaluate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://huggingface.co/google/bert-base-uncased"}'
```

---

## File Changes Summary

| File | Change | Purpose |
|------|--------|---------|
| `.github/workflows/cd.yml` | **Enhanced** | Added AWS deployment stage with lint/test/build/deploy jobs |
| `src/aws/dynamodb_service.py` | **New** | DynamoDB CRUD + change history tracking |
| `src/aws/s3_service.py` | **New** | S3 file/bytes operations + hash verification |
| `src/aws/lambda_handler.py` | **New** | Lambda handler for REST API endpoints |
| `src/aws/__init__.py` | **New** | Module initialization |
| `docs/AWS_DEPLOYMENT.md` | **New** | Complete deployment guide (25+ pages) |
| `requirements.txt` | **Updated** | Added boto3, botocore |

---

## Next Steps

1. ✅ **This**: Run the Quick Start steps above
2. ⏳ Follow the full guide at `docs/AWS_DEPLOYMENT.md`
3. ⏳ Set up CloudFormation template for infrastructure as code
4. ⏳ Add API Gateway endpoint URL to GitHub Secrets
5. ⏳ Create production deployment stage
6. ⏳ Set up auto-scaling and performance monitoring

---

## Support & Debugging

If deployment fails, check:

1. **GitHub Actions logs** → Check what failed (lint, test, deploy)
2. **CloudWatch logs**: 
   ```bash
   aws logs tail /aws/lambda/ml-model-evaluator-staging --follow
   ```
3. **DynamoDB table exists**:
   ```bash
   aws dynamodb describe-table --table-name ml-model-evaluator
   ```
4. **S3 bucket exists**:
   ```bash
   aws s3api head-bucket --bucket ml-evaluator-artifacts
   ```

See `docs/AWS_DEPLOYMENT.md` for detailed troubleshooting.

---

**You're ready to deploy! 🚀**

Push your code and watch GitHub Actions handle the rest!
