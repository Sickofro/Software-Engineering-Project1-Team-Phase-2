# AWS Setup Checklist ✓

## Quick Checklist - Follow in Order

### ✅ Step 1: Install AWS CLI
```
Status: [ ] Not started
        [ ] In progress
        [✅] Complete
        
Command to run:
  pip install awscli

Verify with:
  aws --version
```

### ✅ Step 2: Get AWS Access Keys
```
Status: [ ] Not started
        [ ] In progress
        [✅] Complete

Where: https://console.aws.amazon.com/
1. Sign in to AWS
2. Click account name (top right) → Security Credentials
3. Access keys → Create access key
4. Save these values:
   - Access Key ID: [REDACTED - do NOT store secrets in the repo]
   - Secret Access Key: [REDACTED - do NOT store secrets in the repo]

IMPORTANT: You just added real credentials to this file. They have been redacted above. Next, rotate/delete the exposed keys in the AWS Console immediately (see guidance below). Do NOT share these values.
```

### ✅ Step 3: Configure AWS CLI
```
Status: [ ] Not started
        [✅] In progress
        [ ] Complete

Command to run:
  aws configure

Enter when prompted:
  AWS Access Key ID: [paste from Step 2]
  AWS Secret Access Key: [paste from Step 2]
  Default region: us-east-1
  Default output: json

Verify with:
  aws sts get-caller-identity
```

### ✅ Step 4: Create DynamoDB Table
```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Command to run:
  aws dynamodb create-table \
    --table-name ml-model-evaluator \
    --attribute-definitions AttributeName=id,AttributeType=S \
    --key-schema AttributeName=id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1

Expected: Table creation successful

Verify with:
  aws dynamodb describe-table --table-name ml-model-evaluator
```

### ✅ Step 5: Create S3 Bucket
```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Command 1 (Create bucket):
  aws s3api create-bucket \
    --bucket ml-evaluator-artifacts \
    --region us-east-1

Command 2 (Enable versioning):
  aws s3api put-bucket-versioning \
    --bucket ml-evaluator-artifacts \
    --versioning-configuration Status=Enabled

Verify with:
  aws s3api head-bucket --bucket ml-evaluator-artifacts
```

### ✅ Step 6: Create IAM Role
```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Command 1 (Create trust policy file):
  cat > /tmp/trust-policy.json << 'EOF'
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }
  EOF

Command 2 (Create role):
  aws iam create-role \
    --role-name ml-evaluator-lambda-role \
    --assume-role-policy-document file:///tmp/trust-policy.json

Commands 3-6 (Attach permissions - run all 4):
  aws iam attach-role-policy \
    --role-name ml-evaluator-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess

  aws iam attach-role-policy \
    --role-name ml-evaluator-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

  aws iam attach-role-policy \
    --role-name ml-evaluator-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess

  aws iam attach-role-policy \
    --role-name ml-evaluator-lambda-role \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchMetricsFullAccess

Verify with:
  aws iam get-role --role-name ml-evaluator-lambda-role
```

### ✅ Step 7: Create Lambda Function
```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Command 1 (Get your Account ID):
  aws sts get-caller-identity --query Account --output text
  
Copy the 12-digit number: ________________

Command 2 (Create Lambda function):
Replace YOUR_ACCOUNT_ID with the number you copied above:

  aws lambda create-function \
    --function-name ml-model-evaluator-staging \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/ml-evaluator-lambda-role \
    --handler src.aws.lambda_handler.lambda_handler \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{DYNAMODB_TABLE=ml-model-evaluator,S3_BUCKET=ml-evaluator-artifacts}" \
    --zip-file fileb:///dev/null \
    --region us-east-1

Example (with real account ID):
  aws lambda create-function \
    --function-name ml-model-evaluator-staging \
    --runtime python3.11 \
    --role arn:aws:iam::123456789012:role/ml-evaluator-lambda-role \
    ...

Verify with:
  aws lambda get-function --function-name ml-model-evaluator-staging
```

### ✅ Step 8: Verify Everything
```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Run these 4 verification commands:

1. DynamoDB:
   aws dynamodb describe-table --table-name ml-model-evaluator --query 'Table.TableStatus'
   Expected: ACTIVE

2. S3:
   aws s3api head-bucket --bucket ml-evaluator-artifacts && echo "Bucket exists!"
   Expected: Bucket exists!

3. Lambda:
   aws lambda get-function --function-name ml-model-evaluator-staging --query 'Configuration.FunctionName'
   Expected: ml-model-evaluator-staging

4. IAM Role:
   aws iam get-role --role-name ml-evaluator-lambda-role --query 'Role.RoleName'
   Expected: ml-evaluator-lambda-role
```

---

## Step 9: Add GitHub Secrets

```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Where: GitHub → Your Repo → Settings → Secrets and variables → Actions

Secret 1:
  Name: AWS_ACCESS_KEY_ID
  Value: [from Step 2]

Secret 2:
  Name: AWS_SECRET_ACCESS_KEY
  Value: [from Step 2]

Secret 3 (after first deploy):
  Name: STAGING_API_ENDPOINT
  Value: [will add this later]
```

---

## Step 10: Push Code & Deploy

```
Status: [ ] Not started
        [ ] In progress
        [ ] Complete

Commands:
  git add .
  git commit -m "feat: Add AWS deployment"
  git push origin aman's-branch
  
Then:
  1. Go to GitHub
  2. Create Pull Request
  3. Wait for tests to pass ✓
  4. Merge to main
  5. Watch GitHub Actions deploy!
  6. Check: GitHub → Actions → Latest run
```

---

## Summary

- **Steps 1-8**: Set up AWS resources (~20 minutes)
- **Step 9**: Add GitHub Secrets (~5 minutes)
- **Step 10**: Push code and deploy (~5 minutes)

**Total Time**: ~30 minutes

---

## Getting Help

When you're stuck, tell me:

1. **Which step** (1-10)
2. **The exact error** (copy-paste it)
3. **What you tried** (which command)

Example:
```
I'm stuck on Step 4 (DynamoDB)

Error message:
  "User: arn:aws:iam::123456789012:user/aman is not authorized to perform: 
   dynamodb:CreateTable on resource"

I ran:
  aws dynamodb create-table --table-name ml-model-evaluator ...
```

I'll help you fix it! 🚀
