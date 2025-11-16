# Project 2 - AWS Deployment Documentation

## Quick Navigation

### 🚀 Getting Started
- **[DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md)** ← START HERE
  - 5 quick steps to deploy
  - 15-30 minutes to production
  - Perfect for first-time setup

### 📋 Understanding the System
- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)**
  - What was built and why
  - Key components overview
  - Data models and flow diagrams

- **[WORKFLOW_GUIDE.md](./WORKFLOW_GUIDE.md)**
  - Complete CI/CD workflow
  - Step-by-step examples
  - Real-world deployment scenarios

### 📖 Complete Reference
- **[AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md)**
  - Comprehensive deployment guide
  - All AWS resource setup
  - Troubleshooting and debugging
  - Cost estimation

---

## What Was Built

✅ **GitHub Actions CI/CD Pipeline**
- Automated linting, type checking, testing
- Automatic deployment to AWS on `git push main`
- Smoke tests after deployment

✅ **AWS Lambda API**
- RESTful endpoints for CRUD operations
- Health check endpoint
- Model evaluation endpoint
- Error handling and validation

✅ **DynamoDB Storage**
- Model metadata with audit trails
- Change history tracking
- Immutable record IDs
- Soft delete support

✅ **S3 Artifact Storage**
- Evaluation results storage
- SHA256 integrity verification
- Versioning for audit trail
- File listing and retrieval

✅ **CloudWatch Monitoring**
- Deployment logs
- Error tracking
- Performance metrics
- Health status

---

## Project Structure

```
Software-Engineering-Project1-Team-Phase-2/
├── .github/
│   └── workflows/
│       └── cd.yml                    ← Enhanced with AWS deployment
├── src/
│   ├── aws/                          ← NEW AWS Services
│   │   ├── __init__.py
│   │   ├── dynamodb_service.py      ← CRUD + audit trail
│   │   ├── s3_service.py            ← File storage
│   │   └── lambda_handler.py        ← REST API handler
│   ├── metrics/                      ← Existing metrics
│   ├── models/                       ← Existing models
│   └── utils/                        ← Existing utilities
├── tests/                            ← Existing tests
├── docs/                             ← Documentation
│   ├── README.md                     ← This file
│   ├── DEPLOYMENT_QUICKSTART.md      ← Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md     ← Technical summary
│   ├── WORKFLOW_GUIDE.md             ← Complete workflow
│   └── AWS_DEPLOYMENT.md             ← Full reference
├── main.py                           ← CLI entry point
├── requirements.txt                  ← Updated with boto3
└── README.md                         ← Main project README
```

---

## Phase 2 Requirements Addressed

### ✅ Baseline Requirements
- **CRUD**: REST API endpoints for Create, Read, Update, Delete
- **Ingest**: Pull metadata from HuggingFace/GitHub URLs
- **Enumerate**: List models with filtering

### ✅ Extended Track: High-Assurance
- **Immutable Record IDs**: UUID-based primary keys
- **Change History**: Complete audit trail with version tracking
- **License Policy**: Enforcement on model records
- **Artifact Integrity**: SHA256 hashes on all S3 objects

### ✅ CI/CD Requirements
- **Automated Testing**: pytest runs on every PR
- **Code Quality**: flake8 linting + mypy type checking
- **Automated Deployment**: Push to main → auto-deploy to AWS
- **Coverage**: 60%+ coverage target

### ✅ Observability
- **CloudWatch Logs**: All API calls and errors logged
- **Metrics**: Deployment status and performance tracked
- **Health Endpoint**: `/health` for monitoring

---

## Key Files Modified/Created

### Modified
- `.github/workflows/cd.yml` - Enhanced with AWS deployment stages

### Created
- `src/aws/dynamodb_service.py` - DynamoDB CRUD operations
- `src/aws/s3_service.py` - S3 file operations
- `src/aws/lambda_handler.py` - Lambda REST API handler
- `src/aws/__init__.py` - Module initialization
- `requirements.txt` - Added boto3, botocore

### Documentation
- `docs/DEPLOYMENT_QUICKSTART.md` - 5-step quick start
- `docs/IMPLEMENTATION_SUMMARY.md` - Technical overview
- `docs/WORKFLOW_GUIDE.md` - Complete workflow guide
- `docs/AWS_DEPLOYMENT.md` - Full reference
- `docs/README.md` - This file

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **CI/CD** | GitHub Actions | Automated testing & deployment |
| **Compute** | AWS Lambda | Serverless REST API |
| **Storage** | AWS DynamoDB | Model metadata |
| **Storage** | AWS S3 | Artifact storage |
| **API** | API Gateway | REST endpoint |
| **Monitoring** | CloudWatch | Logs & metrics |
| **Language** | Python 3.11 | Implementation |
| **Testing** | pytest | Unit & integration tests |
| **Linting** | flake8 | Code quality |
| **Types** | mypy | Type safety |

---

## Getting Started

### For First-Time Setup
1. Read **[DEPLOYMENT_QUICKSTART.md](./DEPLOYMENT_QUICKSTART.md)**
2. Create AWS resources (DynamoDB, S3, IAM Role, Lambda)
3. Add GitHub Secrets (AWS credentials)
4. Push code and watch deployment

### For Daily Development
1. Create feature branch
2. Make changes and write tests
3. `git push origin feature/...`
4. Create Pull Request
5. GitHub Actions tests automatically
6. Merge to main
7. Automatic deployment to AWS

### For Monitoring
- Check GitHub Actions logs: GitHub → Actions → Latest run
- View Lambda logs: `aws logs tail /aws/lambda/ml-model-evaluator-staging`
- Test API: `curl https://YOUR_API_GATEWAY_URL/health`

---

## Deployment Timeline

### One-Time Setup (~1 hour)
```
Create AWS resources (15 min)
  → Create IAM role (10 min)
  → Configure GitHub Secrets (5 min)
  → Create API Gateway (15 min)
  → Test deployment (10 min)
```

### Per Deployment (~2-5 minutes)
```
Developer push to main (30 sec)
  → GitHub Actions triggered (1 sec)
  → Tests run (30-60 sec)
  → Build & package (20 sec)
  → Deploy to Lambda (30 sec)
  → Smoke tests (5 sec)
  → Live! (1 sec)
```

---

## Cost Estimate (Monthly)

| Service | Free Tier | Staging Cost |
|---------|-----------|--------------|
| Lambda | 1M requests, 400K seconds | $0 |
| DynamoDB | 25 read/write units | $0-5 |
| S3 | 5GB storage | $0.12 |
| API Gateway | None | $3.50 |
| CloudWatch | 5GB logs | $0.50 |
| **Total** | | **~$4-9/month** |

Most costs covered by free tier for staging!

---

## Support & Troubleshooting

### Common Issues
1. **Tests failing**: Run `python -m pytest tests/ -v` locally
2. **Lambda not deploying**: Check CloudWatch logs
3. **API not responding**: Verify Lambda function exists
4. **DynamoDB errors**: Check table exists and permissions

See **[AWS_DEPLOYMENT.md](./AWS_DEPLOYMENT.md#troubleshooting)** for detailed debugging.

---

## Team Responsibilities

### DevOps/Infrastructure
- [ ] Create AWS resources
- [ ] Configure CloudWatch dashboards
- [ ] Set up alerts and monitoring
- [ ] Document runbooks

### Developers
- [ ] Understand the API (lambda_handler.py)
- [ ] Write tests (60%+ coverage)
- [ ] Follow CI/CD workflow
- [ ] Use feature branches

### Tech Lead
- [ ] Review and approve PRs
- [ ] Monitor deployment status
- [ ] Plan production rollout
- [ ] Optimize performance

---

## Next Steps

1. ✅ **Understand the system** → Read IMPLEMENTATION_SUMMARY.md
2. ⏳ **Set up AWS** → Follow DEPLOYMENT_QUICKSTART.md
3. ⏳ **Deploy code** → Push to main branch
4. ⏳ **Test API** → Call /health and /models endpoints
5. ⏳ **Monitor** → Check CloudWatch logs
6. ⏳ **Scale to production** → Create prod Lambda & API

---

## Questions?

Refer to the relevant documentation:
- **"How do I deploy?"** → DEPLOYMENT_QUICKSTART.md
- **"How does it work?"** → IMPLEMENTATION_SUMMARY.md
- **"What's the workflow?"** → WORKFLOW_GUIDE.md
- **"How do I debug?"** → AWS_DEPLOYMENT.md (Troubleshooting section)
- **"What changed?"** → IMPLEMENTATION_SUMMARY.md (File Changes)

---

**Last Updated**: November 14, 2025  
**Status**: ✅ Ready for Production Deployment
