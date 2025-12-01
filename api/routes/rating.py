"""
Rating endpoint - Integrate Phase 1 metrics calculator
"""
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime

from ..database import get_artifacts_table, get_ratings_table
from src.metrics.calculator import MetricsCalculator
from src.models.model import ModelInfo
from src.url_parser import URLParser

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
metrics_calculator = MetricsCalculator()
url_parser = URLParser()


# ============================================================================
# Pydantic Models (Response Schema)
# ============================================================================

class SizeScore(BaseModel):
    raspberry_pi: float
    jetson_nano: float
    desktop_pc: float
    aws_server: float


class ModelRating(BaseModel):
    name: str
    category: str
    net_score: float
    net_score_latency: float
    ramp_up_time: float
    ramp_up_time_latency: float
    bus_factor: float
    bus_factor_latency: float
    performance_claims: float
    performance_claims_latency: float
    license: float
    license_latency: float
    dataset_and_code_score: float
    dataset_and_code_score_latency: float
    dataset_quality: float
    dataset_quality_latency: float
    code_quality: float
    code_quality_latency: float
    reproducibility: float
    reproducibility_latency: float
    reviewedness: float
    reviewedness_latency: float
    tree_score: float
    tree_score_latency: float
    size_score: SizeScore
    size_score_latency: float


# ============================================================================
# Helper Functions
# ============================================================================

def verify_auth_token(x_authorization: Optional[str]):
    """Verify authentication token"""
    if not x_authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication failed due to invalid or missing AuthenticationToken"
        )
    return True


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/artifact/model/{id}/rate")
async def rate_model(
    id: str,
    x_authorization: str = Header(None, alias="X-Authorization")
) -> ModelRating:
    """
    Get ratings for this model artifact (BASELINE)
    
    Returns comprehensive rating metrics for the specified model.
    """
    verify_auth_token(x_authorization)
    
    try:
        # 1. Get artifact from database
        artifacts_table = get_artifacts_table()
        response = artifacts_table.get_item(Key={'id': id})
        
        if 'Item' not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact does not exist"
            )
        
        artifact = response['Item']
        
        # Verify it's a model
        if artifact.get('type') != 'model':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rating is only supported for model artifacts"
            )
        
        # 2. Check if rating already exists in cache
        ratings_table = get_ratings_table()
        cached_rating = ratings_table.get_item(Key={'artifact_id': id})
        
        if 'Item' in cached_rating:
            logger.info(f"Returning cached rating for artifact {id}")
            item = cached_rating['Item']
            return ModelRating(**item)
        
        # 3. Calculate new rating using Phase 1 metrics
        logger.info(f"Calculating new rating for artifact {id}: {artifact['name']}")
        
        # Parse URL to get model info
        url = artifact['url']
        parsed = url_parser.parse_url(url)
        
        if not parsed or parsed.get('type') != 'model':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid model URL or unable to parse"
            )
        
        # Create ModelInfo object
        model_info = ModelInfo(
            name=artifact['name'],
            url=url,
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        # Calculate all metrics
        import time
        start_time = time.time()
        
        metrics = metrics_calculator.calculate_all_metrics(model_info)
        
        total_latency = time.time() - start_time
        
        # 4. Format response according to OpenAPI spec
        rating = ModelRating(
            name=artifact['name'],
            category="MODEL",
            net_score=metrics.get('net_score', 0.0),
            net_score_latency=total_latency,
            ramp_up_time=metrics.get('ramp_up_time', 0.0),
            ramp_up_time_latency=metrics.get('ramp_up_time_latency', 0.0),
            bus_factor=metrics.get('bus_factor', 0.0),
            bus_factor_latency=metrics.get('bus_factor_latency', 0.0),
            performance_claims=metrics.get('performance_claims', 0.0),
            performance_claims_latency=metrics.get('performance_claims_latency', 0.0),
            license=metrics.get('license', 0.0),
            license_latency=metrics.get('license_latency', 0.0),
            dataset_and_code_score=metrics.get('dataset_and_code_score', 0.0),
            dataset_and_code_score_latency=metrics.get('dataset_and_code_score_latency', 0.0),
            dataset_quality=metrics.get('dataset_quality', 0.0),
            dataset_quality_latency=metrics.get('dataset_quality_latency', 0.0),
            code_quality=metrics.get('code_quality', 0.0),
            code_quality_latency=metrics.get('code_quality_latency', 0.0),
            reproducibility=metrics.get('reproducibility', 0.0),
            reproducibility_latency=metrics.get('reproducibility_latency', 0.0),
            reviewedness=metrics.get('reviewedness', 0.0),
            reviewedness_latency=metrics.get('reviewedness_latency', 0.0),
            tree_score=metrics.get('tree_score', 0.0),
            tree_score_latency=metrics.get('tree_score_latency', 0.0),
            size_score=SizeScore(
                raspberry_pi=metrics.get('size_score', {}).get('raspberry_pi', 0.0),
                jetson_nano=metrics.get('size_score', {}).get('jetson_nano', 0.0),
                desktop_pc=metrics.get('size_score', {}).get('desktop_pc', 0.0),
                aws_server=metrics.get('size_score', {}).get('aws_server', 0.0)
            ),
            size_score_latency=metrics.get('size_score_latency', 0.0)
        )
        
        # 5. Cache the rating in DynamoDB
        rating_dict = rating.model_dump()
        rating_dict['artifact_id'] = id
        rating_dict['computed_at'] = datetime.utcnow().isoformat()
        
        ratings_table.put_item(Item=rating_dict)
        
        logger.info(f"Cached rating for artifact {id}")
        
        return rating
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rate model {id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"The artifact rating system encountered an error: {str(e)}"
        )
