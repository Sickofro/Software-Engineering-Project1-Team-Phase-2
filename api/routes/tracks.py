"""
Tracks endpoint - declares which tracks the team is implementing
"""
from fastapi import APIRouter
from typing import Dict, Any, List

router = APIRouter()


@router.get("/tracks")
async def get_tracks() -> Dict[str, List[str]]:
    """
    Get the list of tracks a student has planned to implement
    
    Returns the list of tracks the student plans to implement.
    Valid tracks:
    - "Performance track"
    - "Access control track" 
    - "High assurance track"
    - "Other Security track"
    """
    return {
        "plannedTracks": [
            # TODO: Update this list based on which tracks you're implementing
            # "Performance track",
            # "Access control track",
            # "High assurance track",
            # "Other Security track"
        ]
    }
