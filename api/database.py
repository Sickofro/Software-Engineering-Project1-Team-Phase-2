"""
Database connection and initialization for DynamoDB
"""
import logging
from .config import settings

logger = logging.getLogger(__name__)

# Check if we should use mock database
USE_MOCK_DB = settings.use_mock_db

if USE_MOCK_DB:
    logger.info("Using Mock DynamoDB (in-memory)")
    from .mock_dynamodb import get_mock_dynamodb
    
    def get_dynamodb_resource():
        """Get Mock DynamoDB resource"""
        return get_mock_dynamodb()
else:
    logger.info("Using Real DynamoDB")
    import boto3
    from botocore.config import Config
    from .config import settings
    
    def get_dynamodb_resource():
        """Get DynamoDB resource (for high-level operations)"""
        # In Lambda, just use default credentials from IAM role
        # Don't pass explicit credentials - let boto3 use the IAM role
        if settings.dynamodb_endpoint_url:
            # Local development with custom endpoint
            return boto3.resource(
                'dynamodb',
                region_name=settings.aws_region,
                endpoint_url=settings.dynamodb_endpoint_url,
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # Lambda - use IAM role credentials automatically
            return boto3.resource('dynamodb', region_name=settings.aws_region)


if not USE_MOCK_DB:
    def get_dynamodb_client():
        """Get DynamoDB client (for low-level operations)"""
        if settings.dynamodb_endpoint_url:
            # Local development with custom endpoint
            return boto3.client(
                'dynamodb',
                region_name=settings.aws_region,
                endpoint_url=settings.dynamodb_endpoint_url,
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy'
            )
        else:
            # Lambda - use IAM role credentials automatically
            return boto3.client('dynamodb', region_name=settings.aws_region)
    
    dynamodb_client = get_dynamodb_client()
else:
    dynamodb_client = None


# Initialize global connection
dynamodb = get_dynamodb_resource()


def get_artifacts_table():
    """Get Artifacts table"""
    return dynamodb.Table(settings.dynamodb_artifacts_table)


def get_ratings_table():
    """Get Ratings table"""
    return dynamodb.Table(settings.dynamodb_ratings_table)


def get_users_table():
    """Get Users table"""
    return dynamodb.Table(settings.dynamodb_users_table)


def get_audit_table():
    """Get Audit Log table"""
    return dynamodb.Table(settings.dynamodb_audit_table)
