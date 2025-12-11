"""
Configuration for the API server
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "ECE 461 Trustworthy Model Registry"
    app_version: str = "3.4.6"
    debug: bool = False
    
    # Database Settings
    use_mock_db: bool = False  # Use real DynamoDB in Lambda
    
    # AWS Settings
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # DynamoDB Settings
    dynamodb_endpoint_url: Optional[str] = None  # For local development
    dynamodb_artifacts_table: str = "Artifacts"
    dynamodb_ratings_table: str = "Ratings"
    dynamodb_users_table: str = "Users"
    dynamodb_audit_table: str = "AuditLog"
    
    # S3 Settings
    s3_bucket_name: str = "ece461-artifacts"
    s3_endpoint_url: Optional[str] = None  # For local development
    
    # Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Default admin user
    default_admin_user: str = "ece30861defaultadminuser"
    default_admin_password: str = "correcthorsebatterystaple123(!__+@**(A'\";DROP TABLE artifacts;"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
