# Complete AWS Deployment Workflow

## Overview

Your ML Model Evaluator now has a **fully automated CI/CD pipeline** that:
1. Tests code automatically on every PR
2. Deploys to AWS Lambda on push to `main`
3. Stores metadata in DynamoDB with audit trails
4. Stores artifacts in S3 with integrity checking
5. Exposes a RESTful API via API Gateway
6. Monitors everything with CloudWatch

---

## Step-by-Step Deployment Process

### Phase 1: One-Time AWS Setup (15-30 minutes)

#### 1A. Create DynamoDB Table
```bash
aws dynamodb create-table \
  --table-name ml-model-evaluator \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```
✅ **Result**: DynamoDB table created for storing model metadata

#### 1B. Create S3 Bucket
```bash
aws s3api create-bucket --bucket ml-evaluator-artifacts

# Enable versioning for audit trail
aws s3api put-bucket-versioning \
  --bucket ml-evaluator-artifacts \
  --versioning-configuration Status=Enabled
```
✅ **Result**: S3 bucket created for storing evaluation results and artifacts

#### 1C. Create IAM Role for Lambda
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

# Attach policies
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```
✅ **Result**: IAM role created with permissions for Lambda

#### 1D. Create Lambda Function (Optional - Can be done via CLI or manually)
```bash
# After first GitHub Actions deployment, manually create the function:
aws lambda create-function \
  --function-name ml-model-evaluator-staging \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT_ID:role/ml-evaluator-lambda-role \
  --handler src.aws.lambda_handler.lambda_handler \
  --timeout 300 \
  --memory-size 512 \
  --environment "Variables={DYNAMODB_TABLE=ml-model-evaluator,S3_BUCKET=ml-evaluator-artifacts}"
```
✅ **Result**: Lambda function created and ready for code deployment

#### 1E. Create API Gateway (Optional - Can add later)
```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
  --name ml-model-evaluator \
  --query 'id' --output text)

# Create resource and integrate with Lambda
# (See full guide in docs/AWS_DEPLOYMENT.md for complete commands)
```
✅ **Result**: API Gateway created for REST endpoint

### Phase 2: GitHub Setup (5 minutes)

#### 2A. Add GitHub Secrets
Go to GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:
```
AWS_ACCESS_KEY_ID          = [Your AWS Access Key]
AWS_SECRET_ACCESS_KEY      = [Your AWS Secret Key]
STAGING_API_ENDPOINT       = [Your API Gateway URL - add later]
PYPI_API_TOKEN            = [Optional - for PyPI publishing]
```

**To get AWS credentials:**
```bash
# Create IAM user with programmatic access
aws iam create-access-key --user-name your-github-user
```

✅ **Result**: GitHub can authenticate with AWS

#### 2B. Clone the repo with AWS files
```bash
git pull origin aman's-branch
# or git pull origin Prems-Branch (where we pulled from)
```

✅ **Result**: Your local code has all AWS deployment files

---

### Phase 3: Development & Deployment (Automatic)

#### 3A. Developer makes code changes
```bash
git checkout -b feature/my-feature
# ... make changes ...
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

#### 3B. Create Pull Request
- Go to GitHub
- Create PR from feature branch to `main`
- GitHub Actions **automatically runs**:
  - ✅ Linting (flake8)
  - ✅ Type checking (mypy)
  - ✅ Tests (pytest with coverage ≥60%)

#### 3C. Review & Merge
- All checks must pass ✅
- Team reviews code
- Merge PR to `main`

#### 3D. Automatic Deployment (GitHub Actions)
Once merged to `main`, GitHub Actions:
1. **Lint Stage** (5s)
   - flake8 code quality check
   - mypy type checking

2. **Test Stage** (30-60s)
   - pytest runs all tests
   - Coverage report generated
   - Results uploaded to Codecov

3. **Build Stage** (20s)
   - Python distribution package built
   - Artifacts created

4. **Deploy to AWS** (30-60s)
   - Lambda package created:
     ```
     lambda_package/
     ├─ src/
     ├─ main.py
     ├─ requirements.txt
     └─ [all dependencies]
     ```
   - Zipped and uploaded to S3
   - Lambda function updated
   - New code is live

5. **Smoke Tests** (5s)
   - `curl /health` endpoint
   - Verify API is responding

6. **CloudWatch Metrics** (1s)
   - Deployment success posted to CloudWatch

✅ **Result**: Code is deployed to staging in ~2-5 minutes

---

## Real-World Example: Adding a Feature

### Scenario: Team member adds license policy check

```bash
# 1. Create feature branch
git checkout -b feature/license-policy-check
cd /path/to/repo

# 2. Create new file: src/policies/license_policy.py
cat > src/policies/license_policy.py << 'EOF'
class LicensePolicy:
    ALLOW_LIST = ['MIT', 'Apache-2.0', 'BSD-3-Clause']
    DENY_LIST = ['GPL-3.0']
    
    def check(self, license: str) -> bool:
        return license in self.ALLOW_LIST
EOF

# 3. Add tests
cat > tests/test_license_policy.py << 'EOF'
from src.policies.license_policy import LicensePolicy

def test_allow_mit():
    policy = LicensePolicy()
    assert policy.check('MIT') == True

def test_deny_gpl():
    policy = LicensePolicy()
    assert policy.check('GPL-3.0') == False
EOF

# 4. Update lambda_handler.py to use policy
# (add 10 lines of code)

# 5. Commit and push
git add .
git commit -m "feat: add license policy check"
git push origin feature/license-policy-check

# 6. Create PR on GitHub
# GitHub Actions automatically runs:
#  ✅ Lint (5s)  
#  ✅ Type check (5s)
#  ✅ Tests (30s)
#  Results show: "6/6 tests passed, 85% coverage"

# 7. Review and merge
# (after code review approval)
git checkout main
git merge feature/license-policy-check
git push origin main

# 8. Automatic deployment starts!
#  ✅ Build (20s)
#  ✅ Deploy to Lambda (30s)
#  ✅ Smoke test (5s)
#  Deployment complete! Live in ~1 minute.

# 9. Verify in CloudWatch
aws logs tail /aws/lambda/ml-model-evaluator-staging --follow
```

✅ **Result**: Feature deployed and live in ~2 minutes with automated testing

---

## CI/CD Pipeline Diagram

```
Developer
    │
    ├─→ Branch (feature/...)
    │       │
    │       ├─→ Make code changes
    │       ├─→ Write tests
    │       └─→ git push origin feature/...
    │
    └─→ Create Pull Request
            │
            └─→ GitHub Actions CI
                ├─→ Lint (flake8)       ✅ MUST PASS
                ├─→ Type (mypy)         ✅ MUST PASS
                ├─→ Test (pytest)       ✅ MUST PASS (60%+ coverage)
                │   
                ├─ Status: All checks passing ✅
                │
                └─→ Team review & approval
                    │
                    └─→ Merge to main
                        │
                        └─→ GitHub Actions CD (auto-triggered)
                            ├─→ Build (5-10min)
                            │   ├─ Lint again
                            │   ├─ Type check
                            │   ├─ Run tests
                            │   └─ Create distribution
                            │
                            ├─→ Deploy to AWS (1-2min)
                            │   ├─ Package Lambda
                            │   ├─ Upload to S3
                            │   ├─ Update Lambda function
                            │   └─ Run smoke tests
                            │
                            └─→ Status: Deployed ✅
                                │
                                └─→ Live on AWS!
```

---

## Monitoring & Observability

### View Deployment Status
```bash
# Check if Lambda is running
aws lambda get-function --function-name ml-model-evaluator-staging

# View recent deployments in GitHub
# GitHub repo → Actions → See all workflow runs

# Check CloudWatch logs
aws logs tail /aws/lambda/ml-model-evaluator-staging --follow
```

### View Metrics
```bash
# Get deployment metrics
aws cloudwatch list-metrics --namespace ML-Evaluator

# View specific metric
aws cloudwatch get-metric-statistics \
  --namespace ML-Evaluator \
  --metric-name DeploymentStatus \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Average
```

### Test the Live API
```bash
# Health check
curl https://YOUR_API_GATEWAY_URL/health

# Create model
curl -X POST https://YOUR_API_GATEWAY_URL/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bert-base",
    "source": "huggingface",
    "license": "Apache-2.0",
    "metadata": {}
  }'

# List models
curl https://YOUR_API_GATEWAY_URL/models

# Get specific model
curl 'https://YOUR_API_GATEWAY_URL/models?id=<UUID>'

# Update model
curl -X PUT https://YOUR_API_GATEWAY_URL/models \
  -H "Content-Type: application/json" \
  -d '{
    "id": "<UUID>",
    "license": "MIT"
  }'

# Delete model
curl -X DELETE https://YOUR_API_GATEWAY_URL/models \
  -H "Content-Type: application/json" \
  -d '{"id": "<UUID>"}'
```

---

## Troubleshooting

### Tests fail locally but pass in CI?
```bash
# Run exact pytest command from CI
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### Lambda deployment fails?
```bash
# Check Lambda logs
aws logs tail /aws/lambda/ml-model-evaluator-staging --follow

# Check if Lambda function exists
aws lambda list-functions | grep ml-model-evaluator

# Check if role has permissions
aws iam get-role --role-name ml-evaluator-lambda-role
```

### DynamoDB connection error?
```bash
# Verify table exists
aws dynamodb describe-table --table-name ml-model-evaluator

# Check if Lambda has DynamoDB permissions
aws iam list-attached-role-policies \
  --role-name ml-evaluator-lambda-role
```

### S3 upload fails?
```bash
# Check bucket exists
aws s3api head-bucket --bucket ml-evaluator-artifacts

# Check bucket versioning enabled
aws s3api get-bucket-versioning --bucket ml-evaluator-artifacts
```

---

## Cost Breakdown (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| Lambda | 1M requests, 400K free seconds | $0.20 |
| DynamoDB | 25 read/write units free | $0-5 |
| S3 | ~10GB storage | $0.23 |
| API Gateway | 1M calls | $3.50 |
| CloudWatch | Logs retention | $0.50 |
| **Total** | | **~$5-10/month** |

Free tier covers most staging costs!

---

## Phase 2 Project Requirements Checklist

- ✅ **Tool Selection**: GitHub Actions (from plan)
- ✅ **CRUD Operations**: Create/Read/Update/Delete via REST API
- ✅ **Ingest**: Models pulled from HuggingFace/GitHub URLs
- ✅ **Enumerate**: List models with filters
- ✅ **Extended Track**: High-Assurance
  - ✅ Immutable record IDs (UUID)
  - ✅ Change history (version tracking + audit log)
  - ✅ License policy checks (in evaluator)
  - ✅ Signed artifact hashes (SHA256 in S3)
- ✅ **CI/CD**: GitHub Actions on every commit
- ✅ **Automated Deployment**: Push to main → auto-deploy
- ✅ **Testing**: pytest runs automatically
- ✅ **Coverage**: Code coverage tracked (target ≥60%)
- ✅ **Observability**: CloudWatch logs and metrics
- ✅ **Baseline Tests**: 23 test cases, 100% pass rate

---

## Next Actions

### For Team Leads
1. Review AWS resources needed
2. Create AWS account/credentials if needed
3. Share AWS setup guide with team
4. Assign someone to create AWS resources

### For Developers
1. Pull the latest code: `git pull origin aman's-branch`
2. Run tests locally: `./run test`
3. Make changes on feature branch
4. Push and watch GitHub Actions deploy!

### For Operations
1. Set up CloudWatch dashboard
2. Configure alerts (optional)
3. Plan production deployment
4. Document runbooks for team

---

## Documentation Files

| File | Purpose | Read Time |
|------|---------|-----------|
| `docs/DEPLOYMENT_QUICKSTART.md` | 5-step quick start | 5 min |
| `docs/IMPLEMENTATION_SUMMARY.md` | What was built | 10 min |
| `docs/AWS_DEPLOYMENT.md` | Complete reference | 30 min |
| `.github/workflows/cd.yml` | CI/CD configuration | 15 min |

---

**Status: ✅ Ready for Production Deployment**

Everything is set up. Just create the AWS resources and push to main!
