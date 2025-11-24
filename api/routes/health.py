"""
Health check endpoints
"""
from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Heartbeat check (BASELINE)
    
    Lightweight liveness probe. Returns HTTP 200 when the registry API is reachable.
    """
    return {"status": "ok"}


@router.get("/health/components")
async def health_components(
    windowMinutes: int = 60,
    includeTimeline: bool = False
) -> Dict[str, Any]:
    """
    Get component health details (NON-BASELINE)
    
    Return per-component health diagnostics, including status, active issues,
    and log references.
    """
    # TODO: Implement comprehensive health monitoring
    return {
        "components": [
            {
                "id": "api",
                "display_name": "API Server",
                "status": "ok",
                "observed_at": "2025-11-23T00:00:00Z",
                "metrics": {
                    "requests_per_minute": 10,
                    "avg_response_time_ms": 150
                }
            },
            {
                "id": "dynamodb",
                "display_name": "DynamoDB",
                "status": "ok",
                "observed_at": "2025-11-23T00:00:00Z"
            },
            {
                "id": "metrics",
                "display_name": "Metrics Calculator",
                "status": "ok",
                "observed_at": "2025-11-23T00:00:00Z"
            }
        ],
        "generated_at": "2025-11-23T00:00:00Z",
        "window_minutes": windowMinutes
    }
