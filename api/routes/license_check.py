"""
License compatibility check endpoint
"""
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel
import logging
import requests
import re

from ..database import get_artifacts_table
from src.metrics.license_metric import LicenseMetric

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class LicenseCheckRequest(BaseModel):
    github_url: str


# ============================================================================
# Helper Functions
# ============================================================================

def verify_auth_token(x_authorization: str):
    """Verify authentication token"""
    if not x_authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication failed due to invalid or missing AuthenticationToken"
        )
    return True


def get_github_license(github_url: str) -> str:
    """
    Fetch license information from a GitHub repository
    
    Args:
        github_url: URL to GitHub repository
        
    Returns:
        License identifier (e.g., 'apache-2.0', 'mit')
    """
    try:
        # Extract owner/repo from URL
        parts = github_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            raise ValueError("Invalid GitHub URL")
        
        owner = parts[0]
        repo = parts[1].split('?')[0]
        
        # Get repository info from GitHub API
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The artifact or GitHub project could not be found."
            )
        elif response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="External license information could not be retrieved."
            )
        
        data = response.json()
        license_info = data.get('license')
        
        if license_info and license_info.get('key'):
            return license_info['key']
        
        return 'unknown'
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch GitHub license: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="External license information could not be retrieved."
        )


def get_huggingface_license(model_url: str) -> str:
    """
    Fetch license information from a HuggingFace model
    
    Args:
        model_url: URL to HuggingFace model
        
    Returns:
        License identifier
    """
    try:
        # Extract model ID from URL
        pattern = r'huggingface\.co/([^?]+)'
        match = re.search(pattern, model_url)
        if not match:
            return 'unknown'
        
        model_id = match.group(1)
        
        # Get model info from HF API
        api_url = f"https://huggingface.co/api/models/{model_id}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            return 'unknown'
        
        data = response.json()
        
        # Check cardData for license
        card_data = data.get('cardData', {})
        license_info = card_data.get('license')
        
        if not license_info:
            # Check in tags
            tags = data.get('tags', [])
            for tag in tags:
                if tag.startswith('license:'):
                    license_info = tag.replace('license:', '')
                    break
        
        if not license_info:
            # Check in main data
            license_info = data.get('license')
        
        return license_info if license_info else 'unknown'
        
    except Exception as e:
        logger.error(f"Failed to fetch HuggingFace license: {str(e)}")
        return 'unknown'


def check_license_compatibility(artifact_license: str, github_license: str) -> bool:
    """
    Check if two licenses are compatible for fine-tuning and inference
    
    Args:
        artifact_license: License of the artifact (model)
        github_license: License of the GitHub code
        
    Returns:
        True if compatible, False otherwise
    """
    # License compatibility matrix
    # Key principle: More permissive licenses (MIT, Apache) are generally compatible
    # GPL licenses have restrictions
    
    artifact_license = artifact_license.lower().strip()
    github_license = github_license.lower().strip()
    
    # Permissive licenses that are generally compatible with everything
    permissive_licenses = ['mit', 'apache-2.0', 'bsd-2-clause', 'bsd-3-clause', 'isc', 'cc-by-4.0']
    
    # If both are permissive, they're compatible
    if artifact_license in permissive_licenses and github_license in permissive_licenses:
        return True
    
    # Apache 2.0 is compatible with most licenses
    if artifact_license == 'apache-2.0' or github_license == 'apache-2.0':
        # Apache is compatible with MIT, BSD, LGPL
        compatible_with_apache = ['mit', 'bsd-2-clause', 'bsd-3-clause', 'lgpl-2.1', 'lgpl-3.0', 'apache-2.0']
        if artifact_license in compatible_with_apache and github_license in compatible_with_apache:
            return True
    
    # MIT is very permissive
    if artifact_license == 'mit' or github_license == 'mit':
        return True
    
    # GPL licenses require derivative works to be GPL
    gpl_licenses = ['gpl-2.0', 'gpl-3.0', 'agpl-3.0']
    
    if artifact_license in gpl_licenses or github_license in gpl_licenses:
        # GPL requires both to be GPL-compatible
        # For simplicity, if either is GPL and the other isn't GPL/LGPL, incompatible
        compatible_with_gpl = gpl_licenses + ['lgpl-2.1', 'lgpl-3.0']
        if artifact_license not in compatible_with_gpl or github_license not in compatible_with_gpl:
            return False
        return True
    
    # LGPL is more permissive than GPL
    lgpl_licenses = ['lgpl-2.1', 'lgpl-3.0']
    if artifact_license in lgpl_licenses or github_license in lgpl_licenses:
        # LGPL is generally compatible with permissive licenses
        return True
    
    # CC licenses
    if 'cc-by' in artifact_license or 'cc-by' in github_license:
        # Creative Commons licenses are generally compatible
        return True
    
    # If unknown, be conservative and return True (benefit of doubt)
    if artifact_license == 'unknown' or github_license == 'unknown':
        return True
    
    # Default: assume compatible if we don't know
    return True


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/artifact/model/{id}/license-check")
async def check_license(
    id: str,
    request: LicenseCheckRequest,
    x_authorization: str = Header(None, alias="X-Authorization")
) -> bool:
    """
    Assess license compatibility for fine-tune and inference usage (BASELINE)
    
    Check if the artifact's license is compatible with a GitHub repository's
    license for fine-tuning and inference purposes.
    
    Args:
        id: Artifact ID
        request: License check request with GitHub URL
        x_authorization: Auth token
        
    Returns:
        True if licenses are compatible, False otherwise
    """
    verify_auth_token(x_authorization)
    
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
        artifact_url = artifact.get('url')
        
        # Get artifact license
        if 'huggingface.co' in artifact_url:
            artifact_license = get_huggingface_license(artifact_url)
        else:
            artifact_license = 'unknown'
        
        logger.info(f"Artifact {id} license: {artifact_license}")
        
        # Get GitHub license
        github_license = get_github_license(request.github_url)
        logger.info(f"GitHub repo license: {github_license}")
        
        # Check compatibility
        is_compatible = check_license_compatibility(artifact_license, github_license)
        
        logger.info(f"License compatibility check: {is_compatible}")
        return is_compatible
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check license compatibility: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The license check request is malformed or references an unsupported usage context."
        )
