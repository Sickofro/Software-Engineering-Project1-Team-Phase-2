"""
Lineage extraction endpoint - Extract artifact dependency graphs
"""
from fastapi import APIRouter, HTTPException, Header, status
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import logging
import requests
import re

from ..database import get_artifacts_table

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class LineageNode(BaseModel):
    artifact_id: Optional[str] = None
    name: str
    source: str
    metadata: Optional[Dict[str, Any]] = None


class LineageEdge(BaseModel):
    from_node_artifact_id: str
    to_node_artifact_id: str
    relationship: str


class LineageGraph(BaseModel):
    nodes: List[LineageNode]
    edges: List[LineageEdge]


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


def generate_pseudo_artifact_id(name: str) -> str:
    """Generate a pseudo artifact ID for external dependencies"""
    # Use hash of name to generate consistent IDs
    return str(abs(hash(name)) % (10 ** 12))


def extract_huggingface_lineage(model_id: str, artifact_id: str) -> LineageGraph:
    """
    Extract lineage from HuggingFace model metadata
    
    Looks for:
    - Base models in config.json
    - Training datasets mentioned in model card
    - Parent models in fine-tuning chains
    """
    nodes = []
    edges = []
    
    try:
        # Add the main artifact as root node
        nodes.append(LineageNode(
            artifact_id=artifact_id,
            name=model_id,
            source="artifact_metadata"
        ))
        
        # Fetch model config from HuggingFace API
        api_url = f"https://huggingface.co/api/models/{model_id}"
        response = requests.get(api_url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Could not fetch model info for {model_id}")
            return LineageGraph(nodes=nodes, edges=edges)
        
        model_data = response.json()
        
        # Extract base model from config if available
        config = model_data.get('config', {})
        if config:
            # Check for base_model_name_or_path
            base_model = config.get('_name_or_path') or config.get('base_model_name_or_path')
            if base_model and base_model != model_id and '/' in base_model:
                base_model_id = generate_pseudo_artifact_id(base_model)
                nodes.append(LineageNode(
                    artifact_id=base_model_id,
                    name=base_model,
                    source="config_json",
                    metadata={"type": "base_model"}
                ))
                edges.append(LineageEdge(
                    from_node_artifact_id=base_model_id,
                    to_node_artifact_id=artifact_id,
                    relationship="base_model"
                ))
        
        # Check model card for dataset mentions
        card_data = model_data.get('cardData', {})
        datasets = card_data.get('datasets', [])
        
        for dataset_name in datasets:
            if dataset_name:
                dataset_id = generate_pseudo_artifact_id(f"dataset:{dataset_name}")
                nodes.append(LineageNode(
                    artifact_id=dataset_id,
                    name=dataset_name,
                    source="model_card",
                    metadata={"type": "training_dataset"}
                ))
                edges.append(LineageEdge(
                    from_node_artifact_id=dataset_id,
                    to_node_artifact_id=artifact_id,
                    relationship="training_dataset"
                ))
        
        # Check tags for architecture information
        tags = model_data.get('tags', [])
        for tag in tags:
            # Look for base model references in tags
            if tag.startswith('base_model:'):
                base_model = tag.replace('base_model:', '')
                if base_model and base_model != model_id:
                    base_model_id = generate_pseudo_artifact_id(base_model)
                    # Check if not already added
                    if not any(n.artifact_id == base_model_id for n in nodes):
                        nodes.append(LineageNode(
                            artifact_id=base_model_id,
                            name=base_model,
                            source="model_tags",
                            metadata={"type": "base_model"}
                        ))
                        edges.append(LineageEdge(
                            from_node_artifact_id=base_model_id,
                            to_node_artifact_id=artifact_id,
                            relationship="base_model"
                        ))
        
        logger.info(f"Extracted lineage for {model_id}: {len(nodes)} nodes, {len(edges)} edges")
        
    except Exception as e:
        logger.error(f"Failed to extract HF lineage for {model_id}: {str(e)}")
    
    return LineageGraph(nodes=nodes, edges=edges)


def extract_github_lineage(repo_url: str, artifact_id: str) -> LineageGraph:
    """
    Extract lineage from GitHub repository
    
    Looks for:
    - Dependencies in requirements.txt, package.json, setup.py
    - Submodules
    """
    nodes = []
    edges = []
    
    try:
        # Extract owner/repo from URL
        parts = repo_url.replace('https://github.com/', '').split('/')
        owner = parts[0]
        repo = parts[1].split('?')[0]
        repo_name = f"{owner}/{repo}"
        
        # Add main artifact as root node
        nodes.append(LineageNode(
            artifact_id=artifact_id,
            name=repo_name,
            source="artifact_metadata"
        ))
        
        # For now, return minimal lineage
        # TODO: Implement actual dependency parsing from repo files
        logger.info(f"Extracted lineage for GitHub repo {repo_name}")
        
    except Exception as e:
        logger.error(f"Failed to extract GitHub lineage: {str(e)}")
    
    return LineageGraph(nodes=nodes, edges=edges)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/artifact/model/{id}/lineage")
async def get_model_lineage(
    id: str,
    x_authorization: str = Header(None, alias="X-Authorization")
) -> LineageGraph:
    """
    Retrieve the lineage graph for this artifact (BASELINE)
    
    Extract dependency relationships from artifact metadata, including:
    - Base models
    - Training datasets
    - Fine-tuning relationships
    
    Args:
        id: Artifact ID
        x_authorization: Auth token
        
    Returns:
        Lineage graph with nodes and edges
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
        artifact_type = artifact.get('type')
        artifact_url = artifact.get('url')
        
        # Extract lineage based on artifact type
        if 'huggingface.co' in artifact_url:
            # Extract model ID from URL
            model_id = artifact.get('name')
            lineage = extract_huggingface_lineage(model_id, id)
        elif 'github.com' in artifact_url:
            lineage = extract_github_lineage(artifact_url, id)
        else:
            # Unknown source, return minimal graph
            lineage = LineageGraph(
                nodes=[LineageNode(
                    artifact_id=id,
                    name=artifact.get('name', 'unknown'),
                    source="artifact_metadata"
                )],
                edges=[]
            )
        
        logger.info(f"Retrieved lineage for artifact {id}: {len(lineage.nodes)} nodes")
        return lineage
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract lineage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The lineage graph cannot be computed because the artifact metadata is missing or malformed."
        )
