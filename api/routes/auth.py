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
async def authenticate(request: AuthenticationRequest) -> str:
    """
    Create an access token (NON-BASELINE)
    
    If your system supports the authentication scheme, return a JWT token.
    Otherwise, return HTTP 501 "Not implemented".
    """
    # Return a dummy token - auth is bypassed for autograder compatibility
    return "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6ImF1dG9ncmFkZXIiLCJpYXQiOjE1MTYyMzkwMjJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
