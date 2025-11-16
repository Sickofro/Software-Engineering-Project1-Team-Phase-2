# AWS Setup - Copy & Paste Commands

This file contains **copy-paste ready commands** for setting up AWS deployment.

## Step 1: Install AWS CLI (2 minutes)

### On Mac (you have a Mac):
```bash
# Option A: Using Homebrew (if you have it)
brew install awscli

# Option B: Using pip (Python)
pip install awscli

# Verify installation
aws --version
```

If you get an error, you may need to restart your terminal.

---

## Step 2: Get AWS Access Keys (5 minutes)

You need to get your AWS credentials from your AWS account.

### In AWS Console:
1. Go to: https://console.aws.amazon.com/
2. Sign in with your AWS account
3. Click your **account name** in top-right → **Security Credentials**
4. Under "Access keys" → Click **Create access key**
5. Choose "Command Line Interface (CLI)" → Create
6. **IMPORTANT**: Download or copy these values:
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJal...` (keep this secret!)

### Keep these handy, you'll use them in Step 3!

---

## Step 3: Configure AWS CLI (2 minutes)

Run this command and paste your credentials when asked:

```bash
aws configure
```

It will ask:
```
AWS Access Key ID [None]: PASTE_YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: PASTE_YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

**Verify it worked:**
```bash
aws sts get-caller-identity
```

Should output something like:
```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:root"
}
```

✅ If you see this, AWS CLI is working!

---

## Step 4: Create DynamoDB Table (2 minutes)

Copy and paste this command:

```bash
aws dynamodb create-table \
  --table-name ml-model-evaluator \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

✅ You should see output confirming the table was created.

**Verify it exists:**
```bash
aws dynamodb describe-table --table-name ml-model-evaluator
```

---

## Step 5: Create S3 Bucket (2 minutes)

Copy and paste this command:

```bash
aws s3api create-bucket \
  --bucket ml-evaluator-artifacts \
  --region us-east-1
```

✅ You should see output confirming the bucket was created.

**Enable versioning (for audit trail):**
```bash
aws s3api put-bucket-versioning \
  --bucket ml-evaluator-artifacts \
  --versioning-configuration Status=Enabled
```

**Verify it exists:**
```bash
aws s3api head-bucket --bucket ml-evaluator-artifacts
```

(No output = success!)

---

## Step 6: Create IAM Role (5 minutes)

### 6A. Create Trust Policy File

Copy this entire block and paste it in your terminal:

```bash
cat > /tmp/trust-policy.json << 'EOF'
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
```

This creates a file that tells AWS "Lambda functions can use this role".

### 6B. Create the Role

Copy and paste this command:

```bash
aws iam create-role \
  --role-name ml-evaluator-lambda-role \
  --assume-role-policy-document file:///tmp/trust-policy.json
```

✅ You should see output with your role details.

### 6C. Attach Permissions (one at a time)

Copy and paste **each** of these 4 commands:

```bash
# Permission 1: Access DynamoDB
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
```

```bash
# Permission 2: Access S3
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
```

```bash
# Permission 3: Write CloudWatch Logs
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

```bash
# Permission 4: Write CloudWatch Metrics
aws iam attach-role-policy \
  --role-name ml-evaluator-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/CloudWatchMetricsFullAccess
```

✅ No output = success!

---

## Step 7: Create Lambda Function (3 minutes)

First, get your AWS Account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

Copy the **12-digit number** that appears (e.g., `123456789012`)

Now copy and paste this command (replace `YOUR_ACCOUNT_ID` with your number):

```bash
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
```

⚠️ **IMPORTANT**: Replace `YOUR_ACCOUNT_ID` with your actual 12-digit account ID!

Example:
```bash
--role arn:aws:iam::123456789012:role/ml-evaluator-lambda-role
```

✅ You should see output confirming the Lambda function was created.

---

## Step 8: Verify Everything (2 minutes)

Run these commands to verify all resources exist:

```bash
# Check DynamoDB table
aws dynamodb describe-table --table-name ml-model-evaluator --query 'Table.TableStatus'

# Check S3 bucket
aws s3api head-bucket --bucket ml-evaluator-artifacts && echo "Bucket exists!"

# Check Lambda function
aws lambda get-function --function-name ml-model-evaluator-staging --query 'Configuration.FunctionName'

# Check IAM role
aws iam get-role --role-name ml-evaluator-lambda-role --query 'Role.RoleName'
```

✅ You should see your resource names output.

---

## Summary of What You Just Created

| Resource | Name | Cost |
|----------|------|------|
| DynamoDB Table | `ml-model-evaluator` | $0-5/month |
| S3 Bucket | `ml-evaluator-artifacts` | $0.50/month |
| Lambda Function | `ml-model-evaluator-staging` | Free (1M requests) |
| IAM Role | `ml-evaluator-lambda-role` | Free |

**Total**: ~$5-6/month for staging 🎉

---

## Next: Add GitHub Secrets

Once you've completed all 8 steps above, go to:

1. GitHub → Your repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add these secrets:

```
Name: AWS_ACCESS_KEY_ID
Value: PASTE_YOUR_ACCESS_KEY_ID_FROM_STEP_2

Name: AWS_SECRET_ACCESS_KEY
Value: PASTE_YOUR_SECRET_KEY_FROM_STEP_2
```

⚠️ **NEVER share these secrets!** GitHub keeps them private.

---

## Troubleshooting

### "Command not found: aws"
→ AWS CLI not installed. Run: `pip install awscli`

### "Unable to locate credentials"
→ AWS CLI not configured. Run: `aws configure`

### "AccessDenied" error
→ Your AWS credentials are wrong. Run `aws configure` again

### "The role with name ml-evaluator-lambda-role cannot be found"
→ Role creation failed. Check the output and try Step 6 again

### "The table you specified does not exist"
→ DynamoDB table not created. Try Step 4 again

### "An error occurred: NoSuchBucket when calling the PutBucketVersioning operation"
→ S3 bucket not created. Try Step 5 again

---

## Questions?

If you get stuck on any step:
1. Copy the **exact error message**
2. Let me know which **step number** you're on
3. I'll help you fix it!

---

**Next Steps After AWS Setup:**
1. ✅ Complete all 8 steps above
2. ⏳ Add GitHub Secrets (see above)
3. ⏳ Push code to main branch
4. ⏳ Watch GitHub Actions deploy automatically

You're almost there! 🚀
