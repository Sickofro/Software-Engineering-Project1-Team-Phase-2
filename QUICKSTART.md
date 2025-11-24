# Phase 2 Quick Start Checklist

Follow these steps to get the API running locally:

## ✅ Step-by-Step Setup

### 1. Install API Dependencies
```bash
pip install -r requirements-api.txt
```
**Expected**: ~2 minutes to install FastAPI, boto3, pydantic, etc.

### 2. Start Local DynamoDB
```bash
# Option A: Docker (recommended)
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# Option B: Check if already running
docker ps | grep dynamodb
```
**Expected**: DynamoDB Local running on port 8000

### 3. Create Database Tables
```bash
python scripts/create_dynamodb_tables.py --local
```
**Expected**: See "✓ All tables created/verified successfully!"

### 4. Set Up Environment
```bash
cp .env.example .env
# Edit .env if needed (defaults work for local dev)
```

### 5. Run the API Server
```bash
python -m api.main
```
**Expected**: 
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### 6. Test the API
Open browser to: **http://localhost:8080/docs**

Try these endpoints:
- `GET /health` - Should return `{"status": "ok"}`
- `GET /tracks` - Should return your planned tracks
- `POST /artifact/model` - Create a test artifact

## 🧪 Quick API Test

```bash
# Test health endpoint
curl http://localhost:8080/health

# Create an artifact
curl -X POST http://localhost:8080/artifact/model \
  -H "X-Authorization: test-token" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://huggingface.co/google-bert/bert-base-uncased"}'

# List all artifacts
curl -X POST http://localhost:8080/artifacts \
  -H "X-Authorization: test-token" \
  -H "Content-Type: application/json" \
  -d '[{"name": "*"}]'
```

## 📝 What's Working vs TODO

### ✅ Working Now (BASELINE)
- Health check
- Create artifacts
- List artifacts
- Get artifact by ID
- Update artifact
- Search by name/regex
- Delete artifact

### ⏳ TODO (BASELINE - Critical)
- **Rating endpoint** - Needs integration with Phase 1 metrics
- **Cost endpoint** - Calculate download sizes
- **Lineage endpoint** - Parse model configs
- **License check** - Check compatibility

### ⏳ TODO (NON-BASELINE - Optional)
- JWT authentication
- Audit trail endpoint
- Health components with real metrics

## 🔧 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'fastapi'
**Solution**: Run `pip install -r requirements-api.txt`

### Issue: Connection refused to localhost:8000
**Solution**: Start DynamoDB Local with docker command above

### Issue: ResourceNotFoundException when creating artifact
**Solution**: Run `python scripts/create_dynamodb_tables.py --local`

### Issue: Import errors in VSCode
**Solution**: These are normal until dependencies are installed. They don't affect runtime.

## 📍 You Are Here

```
[✅ Phase 1 Complete] → [✅ API Foundation] → [⏳ Rating Integration] → [Deployment]
```

**Next Priority**: Implement the rating endpoint to integrate Phase 1 metrics!

## 🚀 Next Session Goals

1. **Implement Rating Endpoint** (~30 min)
   - Create rating.py route
   - Integrate MetricsCalculator
   - Return proper format

2. **Implement Cost Endpoint** (~20 min)
   - Calculate artifact sizes
   - Handle dependencies

3. **Implement Lineage Endpoint** (~30 min)
   - Parse config.json from HuggingFace
   - Build lineage graph

4. **Test Everything** (~20 min)
   - Write tests
   - Verify against OpenAPI spec

**Total Estimated Time**: ~2 hours to complete BASELINE requirements

---

**Questions?** Check `API_DEV_GUIDE.md` or `PHASE2_SUMMARY.md` for more details.
