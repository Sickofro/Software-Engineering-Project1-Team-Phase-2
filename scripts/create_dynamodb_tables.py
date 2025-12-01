#!/usr/bin/env python3
"""
Create DynamoDB tables for Phase 2 API

Run this script to initialize local or AWS DynamoDB tables.

Usage:
    python scripts/create_dynamodb_tables.py [--local]
"""

import boto3
import argparse
import sys
from botocore.exceptions import ClientError


def create_tables(endpoint_url=None, region='us-east-1'):
    """Create all required DynamoDB tables"""
    
    # Initialize DynamoDB resource
    kwargs = {'region_name': region}
    if endpoint_url:
        kwargs['endpoint_url'] = endpoint_url
        kwargs['aws_access_key_id'] = 'dummy'
        kwargs['aws_secret_access_key'] = 'dummy'
        print(f"Using local DynamoDB at {endpoint_url}")
    else:
        print(f"Using AWS DynamoDB in region {region}")
    
    dynamodb = boto3.resource('dynamodb', **kwargs)
    
    # Table 1: Artifacts
    print("\nCreating Artifacts table...")
    try:
        artifacts_table = dynamodb.create_table(
            TableName='Artifacts',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'name', 'AttributeType': 'S'},
                {'AttributeName': 'type', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'name-index',
                    'KeySchema': [
                        {'AttributeName': 'name', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                },
                {
                    'IndexName': 'type-name-index',
                    'KeySchema': [
                        {'AttributeName': 'type', 'KeyType': 'HASH'},
                        {'AttributeName': 'name', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✓ Artifacts table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠ Artifacts table already exists")
        else:
            print(f"✗ Error creating Artifacts table: {e}")
            raise
    
    # Table 2: Ratings
    print("\nCreating Ratings table...")
    try:
        ratings_table = dynamodb.create_table(
            TableName='Ratings',
            KeySchema=[
                {'AttributeName': 'artifact_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'artifact_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✓ Ratings table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠ Ratings table already exists")
        else:
            print(f"✗ Error creating Ratings table: {e}")
            raise
    
    # Table 3: Users
    print("\nCreating Users table...")
    try:
        users_table = dynamodb.create_table(
            TableName='Users',
            KeySchema=[
                {'AttributeName': 'name', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'name', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✓ Users table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠ Users table already exists")
        else:
            print(f"✗ Error creating Users table: {e}")
            raise
    
    # Table 4: AuditLog
    print("\nCreating AuditLog table...")
    try:
        audit_table = dynamodb.create_table(
            TableName='AuditLog',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'artifact_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'artifact-audit-index',
                    'KeySchema': [
                        {'AttributeName': 'artifact_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'},
                    'ProvisionedThroughput': {
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print("✓ AuditLog table created successfully")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("⚠ AuditLog table already exists")
        else:
            print(f"✗ Error creating AuditLog table: {e}")
            raise
    
    print("\n" + "="*60)
    print("✓ All tables created/verified successfully!")
    print("="*60)
    
    # List tables
    print("\nExisting tables:")
    client = boto3.client('dynamodb', **kwargs)
    tables = client.list_tables()
    for table_name in tables['TableNames']:
        print(f"  - {table_name}")


def main():
    parser = argparse.ArgumentParser(description='Create DynamoDB tables for Phase 2 API')
    parser.add_argument(
        '--local',
        action='store_true',
        help='Use local DynamoDB (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--endpoint',
        default='http://localhost:8000',
        help='DynamoDB endpoint URL (for local development)'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.local:
            create_tables(endpoint_url=args.endpoint, region=args.region)
        else:
            print("WARNING: This will create tables in AWS DynamoDB.")
            response = input("Continue? (yes/no): ")
            if response.lower() == 'yes':
                create_tables(region=args.region)
            else:
                print("Aborted.")
                sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
