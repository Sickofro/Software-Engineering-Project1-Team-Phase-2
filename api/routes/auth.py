"""
Authentication endpoints
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class User(BaseModel):
    name: str
    is_admin: bool


class UserAuthenticationInfo(BaseModel):
    password: str


class AuthenticationRequest(BaseModel):
    user: User
    secret: UserAuthenticationInfo


@router.put("/authenticate")
async def authenticate(request: AuthenticationRequest) -> dict:
    """
    Create an access token (NON-BASELINE)
    
    If your system supports the authentication scheme, return a JWT token.
    Otherwise, return HTTP 501 "Not implemented".
    """
    # TODO: Implement JWT authentication
    # For now, return 501
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not yet implemented"
    )
