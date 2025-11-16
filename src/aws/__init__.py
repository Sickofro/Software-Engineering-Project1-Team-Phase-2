# src/aws/__init__.py
"""AWS services for ML Model Evaluator"""

from .dynamodb_service import DynamoDBService
from .s3_service import S3Service

__all__ = ['DynamoDBService', 'S3Service']
