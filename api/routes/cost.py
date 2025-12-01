"""
Cost calculation endpoint - Calculate artifact download sizes
"""
from fastapi import APIRouter, HTTPException, Header, Query, status
from typing import Dict, Optional
import logging
import requests
from urllib.parse import urljoin

from ..database import get_artifacts_table

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_auth_token(x_authorization: Optional[str]):
    """Verify authentication token"""
    if not x_authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication failed due to invalid or missing AuthenticationToken"
        )
    return True


def calculate_huggingface_size(repo_url: str) -> float:
    """
    Calculate the total size of a HuggingFace repository in MB
    
    Args:
        repo_url: URL to the HuggingFace model/dataset
        
    Returns:
        Size in MB
    """
    try:
        # Extract model/dataset ID from URL
        # Format: https://huggingface.co/{org}/{model}
        parts = repo_url.replace('https://huggingface.co/', '').split('/')
        if 'datasets' in parts:
            # Dataset URL
            parts.remove('datasets')
            repo_id = '/'.join(parts[:2])
            api_url = f"https://huggingface.co/api/datasets/{repo_id}"
        else:
            # Model URL
            repo_id = '/'.join(parts[:2])
            api_url = f"https://huggingface.co/api/models/{repo_id}"
        
        # Get repository info from HF API
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Could not fetch HF repo info for {repo_url}")
            return 100.0  # Default fallback size
        
        data = response.json()
        
        # Try to get size from siblings (files in repo)
        total_size_bytes = 0
        siblings = data.get('siblings', [])
        
        for file in siblings:
            size = file.get('size', 0)
            if size:
                total_size_bytes += size
        
        # Convert bytes to MB
        size_mb = total_size_bytes / (1024 * 1024)
        
        # If no size info available, use a default estimate
        if size_mb == 0:
            size_mb = 100.0  # Default estimate for models without size info
            logger.info(f"No size info for {repo_url}, using default {size_mb} MB")
        
        return round(size_mb, 2)
        
    except Exception as e:
        logger.error(f"Failed to calculate HF size for {repo_url}: {str(e)}")
        return 100.0  # Default fallback


def calculate_github_size(repo_url: str) -> float:
    """
    Calculate the total size of a GitHub repository in MB
    
    Args:
        repo_url: URL to the GitHub repository
        
    Returns:
        Size in MB
    """
    try:
        # Extract owner/repo from URL
        # Format: https://github.com/{owner}/{repo}
        parts = repo_url.replace('https://github.com/', '').split('/')
        owner = parts[0]
        repo = parts[1].split('?')[0]  # Remove any query params
        
        # Get repository info from GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Could not fetch GitHub repo info for {repo_url}")
            return 50.0  # Default fallback
        
        data = response.json()
        size_kb = data.get('size', 0)
        
        # GitHub API returns size in KB, convert to MB
        size_mb = size_kb / 1024
        
        if size_mb == 0:
            size_mb = 50.0  # Default estimate
            logger.info(f"No size info for {repo_url}, using default {size_mb} MB")
        
        return round(size_mb, 2)
        
    except Exception as e:
        logger.error(f"Failed to calculate GitHub size for {repo_url}: {str(e)}")
        return 50.0  # Default fallback


def calculate_artifact_cost(url: str) -> float:
    """
    Calculate the cost (download size) of an artifact
    
    Args:
        url: URL to the artifact
        
    Returns:
        Size in MB
    """
    try:
        if 'huggingface.co' in url:
            return calculate_huggingface_size(url)
        elif 'github.com' in url:
            return calculate_github_size(url)
        else:
            logger.warning(f"Unknown URL type: {url}, using default size")
            return 100.0  # Default for unknown sources
            
    except Exception as e:
        logger.error(f"Failed to calculate cost for {url}: {str(e)}")
        return 100.0  # Default fallback


@router.get("/artifact/{artifact_type}/{id}/cost")
async def get_artifact_cost(
    artifact_type: str,
    id: str,
    dependency: bool = Query(False),
    x_authorization: str = Header(None, alias="X-Authorization")
) -> Dict[str, Dict[str, float]]:
    """
    Get the cost of an artifact (BASELINE)
    
    Calculate the total download size (in MB) required for the artifact,
    optionally including dependencies.
    
    Args:
        artifact_type: Type of artifact (model/dataset/code)
        id: Artifact ID
        dependency: If true, include dependency costs
        x_authorization: Auth token
        
    Returns:
        Dictionary mapping artifact IDs to their costs
    """
    verify_auth_token(x_authorization)
    
    # Validate artifact type
    if artifact_type not in ["model", "dataset", "code"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid artifact type. Must be 'model', 'dataset', or 'code'"
        )
    
    try:
        # Get artifact from database
        artifacts_table = get_artifacts_table()
        response = artifacts_table.get_item(Key={'id': id})
        
        if 'Item' not in response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artifact does not exist"
            )
        
        artifact = response['Item']
        
        # Verify artifact type matches
        if artifact.get('type') != artifact_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Artifact {id} is not of type {artifact_type}"
            )
        
        # Calculate standalone cost
        artifact_url = artifact.get('url')
        standalone_cost = calculate_artifact_cost(artifact_url)
        
        # For now, we don't have dependency tracking implemented
        # So we'll just return the standalone cost
        if dependency:
            # TODO: Implement dependency resolution and cost calculation
            # For now, just return the artifact's own cost
            result = {
                id: {
                    "standalone_cost": standalone_cost,
                    "total_cost": standalone_cost
                }
            }
        else:
            result = {
                id: {
                    "total_cost": standalone_cost
                }
            }
        
        logger.info(f"Calculated cost for artifact {id}: {standalone_cost} MB")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate artifact cost: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The artifact cost calculator encountered an error."
        )
