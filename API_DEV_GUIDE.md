# Phase 2 API Development Guide

## Quick Start

### 1. Install API Dependencies

```bash
# Install all API dependencies
pip install -r requirements-api.txt
```

### 2. Set Up Local DynamoDB

**Option A: Using Docker (Recommended)**
```bash
# Run DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# In another terminal, create tables
python scripts/create_dynamodb_tables.py
```

**Option B: Using docker-compose**
```bash
docker-compose up -d dynamodb-local
python scripts/create_dynamodb_tables.py
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your settings (defaults work for local dev)
```

### 4. Run the API Server

```bash
# Development mode with auto-reload
python -m api.main

# Or use uvicorn directly
uvicorn api.main:app --reload --port 8080
```

### 5. Test the API

Open your browser to:
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

## API Structure

```
api/
├── main.py              # FastAPI app entry point
├── config.py            # Configuration settings
├── database.py          # DynamoDB connection
├── routes/              # API endpoints
│   ├── health.py        # Health checks
│   ├── artifacts.py     # Artifact CRUD operations
│   ├── auth.py          # Authentication
│   └── tracks.py        # Tracks declaration
├── schemas/             # Pydantic models (TODO)
└── crud/                # CRUD operations (TODO)
```

## Development Workflow

### Testing Endpoints

Using curl:
```bash
# Health check
curl http://localhost:8080/health

# List all artifacts
curl -X POST http://localhost:8080/artifacts \
  -H "X-Authorization: test-token" \
  -H "Content-Type: application/json" \
  -d '[{"name": "*"}]'

# Create an artifact
curl -X POST http://localhost:8080/artifact/model \
  -H "X-Authorization: test-token" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://huggingface.co/google-bert/bert-base-uncased"}'
```

Using Python:
```python
import requests

# Health check
response = requests.get("http://localhost:8080/health")
print(response.json())

# Create artifact
response = requests.post(
    "http://localhost:8080/artifact/model",
    headers={"X-Authorization": "test-token"},
    json={"url": "https://huggingface.co/google-bert/bert-base-uncased"}
)
print(response.json())
```

## TODO: Next Steps

1. **Create DynamoDB tables script** - `scripts/create_dynamodb_tables.py`
2. **Implement rating endpoint** - Integrate Phase 1 metrics
3. **Add cost calculation endpoint** - Calculate artifact sizes
4. **Implement lineage endpoint** - Parse model config
5. **Add license check endpoint** - Check license compatibility
6. **Implement JWT authentication** - Secure endpoints
7. **Add comprehensive tests** - Test all endpoints
8. **Deploy to AWS** - Production deployment

## Available Endpoints

### BASELINE (Must Implement)

- ✅ `GET /health` - Health check
- ✅ `DELETE /reset` - Reset registry
- ✅ `POST /artifacts` - List/search artifacts
- ✅ `POST /artifact/{artifact_type}` - Create artifact
- ✅ `GET /artifacts/{artifact_type}/{id}` - Get artifact
- ✅ `PUT /artifacts/{artifact_type}/{id}` - Update artifact
- ⏳ `GET /artifact/model/{id}/rate` - Get ratings (TODO)
- ⏳ `GET /artifact/{artifact_type}/{id}/cost` - Get cost (TODO)
- ✅ `POST /artifact/byRegEx` - Search by regex
- ⏳ `GET /artifact/model/{id}/lineage` - Get lineage (TODO)
- ⏳ `POST /artifact/model/{id}/license-check` - License check (TODO)
- ✅ `GET /tracks` - Get tracks

### NON-BASELINE (Optional)

- ⏳ `PUT /authenticate` - Authentication
- ✅ `DELETE /artifacts/{artifact_type}/{id}` - Delete artifact
- ✅ `GET /artifact/byName/{name}` - Search by name
- ⏳ `GET /artifact/{artifact_type}/{id}/audit` - Audit trail (TODO)
- ✅ `GET /health/components` - Component health

## Notes

- Import errors in IDE are normal until dependencies are installed
- DynamoDB must be running before starting the API
- Default admin credentials are in `.env` (from spec)
- Authentication is placeholder for now (returns 501)
