# src/aws/s3_service.py
"""
AWS S3 service for storing model artifacts and blobs
"""

import io
import hashlib
from typing import Optional, BinaryIO, Dict
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from ..utils.logger import setup_logger

class S3Service:
    """Service for interacting with S3"""
    
    def __init__(self, bucket_name: str = "ml-evaluator-artifacts", region: str = "us-east-1"):
        self.logger = setup_logger()
        self.bucket_name = bucket_name
        self.s3_client = boto3.client('s3', region_name=region)
        self.s3_resource = boto3.resource('s3', region_name=region)
    
    def upload_file(self, file_path: str, key: str, metadata: Optional[dict] = None) -> Dict[str, str]:
        """Upload a file to S3"""
        try:
            # Calculate file hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['file-hash'] = file_hash
            s3_metadata['uploaded-at'] = datetime.utcnow().isoformat()
            
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                key,
                ExtraArgs={'Metadata': s3_metadata}
            )
            
            self.logger.info(f"Uploaded {file_path} to s3://{self.bucket_name}/{key}")
            
            return {
                'bucket': self.bucket_name,
                'key': key,
                'hash': file_hash,
                'uploaded_at': s3_metadata['uploaded-at']
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to upload file to S3: {str(e)}")
            raise
    
    def upload_bytes(self, data: bytes, key: str, metadata: Optional[dict] = None) -> Dict[str, str]:
        """Upload bytes to S3"""
        try:
            # Calculate data hash
            data_hash = hashlib.sha256(data).hexdigest()
            
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['data-hash'] = data_hash
            s3_metadata['uploaded-at'] = datetime.utcnow().isoformat()
            
            # Upload bytes
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                Metadata=s3_metadata
            )
            
            self.logger.info(f"Uploaded {len(data)} bytes to s3://{self.bucket_name}/{key}")
            
            return {
                'bucket': self.bucket_name,
                'key': key,
                'hash': data_hash,
                'size_bytes': len(data),
                'uploaded_at': s3_metadata['uploaded-at']
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to upload bytes to S3: {str(e)}")
            raise
    
    def download_file(self, key: str, file_path: str) -> Dict[str, str]:
        """Download a file from S3"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                key,
                file_path
            )
            
            # Verify hash if available
            obj_response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            metadata = obj_response.get('Metadata', {})
            
            self.logger.info(f"Downloaded s3://{self.bucket_name}/{key} to {file_path}")
            
            return {
                'bucket': self.bucket_name,
                'key': key,
                'file_path': file_path,
                'size_bytes': obj_response.get('ContentLength'),
                'hash': metadata.get('file-hash', 'unknown')
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to download file from S3: {str(e)}")
            raise
    
    def download_bytes(self, key: str) -> bytes:
        """Download bytes from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = response['Body'].read()
            
            self.logger.info(f"Downloaded {len(data)} bytes from s3://{self.bucket_name}/{key}")
            return data
            
        except ClientError as e:
            self.logger.error(f"Failed to download bytes from S3: {str(e)}")
            raise
    
    def get_file_hash(self, key: str) -> Optional[str]:
        """Get the hash of a file in S3 without downloading"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            metadata = response.get('Metadata', {})
            return metadata.get('file-hash') or metadata.get('data-hash')
            
        except ClientError as e:
            self.logger.error(f"Failed to get file hash for {key}: {str(e)}")
            return None
    
    def delete_file(self, key: str) -> None:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            self.logger.info(f"Deleted s3://{self.bucket_name}/{key}")
            
        except ClientError as e:
            self.logger.error(f"Failed to delete file from S3: {str(e)}")
            raise
    
    def list_files(self, prefix: str = "", max_keys: int = 100) -> list:
        """List files in S3 with optional prefix"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size_bytes': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'storage_class': obj['StorageClass']
                    })
            
            self.logger.info(f"Listed {len(files)} files from {prefix}")
            return files
            
        except ClientError as e:
            self.logger.error(f"Failed to list files from S3: {str(e)}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
