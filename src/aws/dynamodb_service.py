# src/aws/dynamodb_service.py
"""
AWS DynamoDB service for storing model metadata
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError
from ..utils.logger import setup_logger

class DynamoDBService:
    """Service for interacting with DynamoDB"""
    
    def __init__(self, table_name: str = "ml-model-evaluator", region: str = "us-east-1"):
        self.logger = setup_logger()
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def create_item(self, name: str, source: str, license: str, 
                   metadata: Dict[str, Any], risk_notes: str = "") -> Dict[str, Any]:
        """Create a new model record in DynamoDB"""
        try:
            item_id = str(uuid4())
            timestamp = datetime.utcnow().isoformat()
            
            item = {
                'id': item_id,
                'name': name,
                'source': source,
                'license': license,
                'risk_notes': risk_notes,
                'metadata': metadata,
                'state': 'active',
                'created_at': timestamp,
                'updated_at': timestamp,
                'version': 1,
                'change_history': [
                    {
                        'version': 1,
                        'action': 'CREATE',
                        'timestamp': timestamp,
                        'changed_by': 'system'
                    }
                ]
            }
            
            self.table.put_item(Item=item)
            self.logger.info(f"Created item {item_id}: {name}")
            return item
            
        except ClientError as e:
            self.logger.error(f"Failed to create item: {str(e)}")
            raise
    
    def read_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Read a model record from DynamoDB"""
        try:
            response = self.table.get_item(Key={'id': item_id})
            
            if 'Item' not in response:
                self.logger.warning(f"Item {item_id} not found")
                return None
            
            return response['Item']
            
        except ClientError as e:
            self.logger.error(f"Failed to read item {item_id}: {str(e)}")
            raise
    
    def update_item(self, item_id: str, updates: Dict[str, Any], 
                   changed_by: str = "system") -> Dict[str, Any]:
        """Update a model record in DynamoDB"""
        try:
            # Get current item first to add to change history
            current_item = self.read_item(item_id)
            if not current_item:
                raise ValueError(f"Item {item_id} not found")
            
            timestamp = datetime.utcnow().isoformat()
            new_version = current_item.get('version', 1) + 1
            
            # Build update expression
            update_expr_parts = []
            expr_attr_values = {}
            expr_attr_names = {}
            
            for key, value in updates.items():
                if key not in ['id', 'created_at', 'state']:  # Immutable fields
                    placeholder = f":{key}"
                    update_expr_parts.append(f"{key} = {placeholder}")
                    expr_attr_values[placeholder] = value
            
            # Add version and updated_at
            update_expr_parts.append(f"#v = :version")
            update_expr_parts.append(f"updated_at = :updated_at")
            expr_attr_names['#v'] = 'version'
            expr_attr_values[':version'] = new_version
            expr_attr_values[':updated_at'] = timestamp
            
            # Add change history entry
            change_entry = {
                'version': new_version,
                'action': 'UPDATE',
                'timestamp': timestamp,
                'changed_by': changed_by,
                'fields_changed': list(updates.keys())
            }
            
            update_expr = "SET " + ", ".join(update_expr_parts)
            update_expr += " ADD change_history :change_entry"
            expr_attr_values[':change_entry'] = {change_entry}
            
            response = self.table.update_item(
                Key={'id': item_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues='ALL_NEW'
            )
            
            self.logger.info(f"Updated item {item_id}, version now {new_version}")
            return response['Attributes']
            
        except ClientError as e:
            self.logger.error(f"Failed to update item {item_id}: {str(e)}")
            raise
    
    def delete_item(self, item_id: str, changed_by: str = "system") -> None:
        """Soft delete a model record (mark as inactive)"""
        try:
            timestamp = datetime.utcnow().isoformat()
            current_item = self.read_item(item_id)
            
            if not current_item:
                raise ValueError(f"Item {item_id} not found")
            
            new_version = current_item.get('version', 1) + 1
            
            change_entry = {
                'version': new_version,
                'action': 'DELETE',
                'timestamp': timestamp,
                'changed_by': changed_by
            }
            
            self.table.update_item(
                Key={'id': item_id},
                UpdateExpression="SET #state = :state, #v = :version, updated_at = :updated_at ADD change_history :change_entry",
                ExpressionAttributeNames={
                    '#state': 'state',
                    '#v': 'version'
                },
                ExpressionAttributeValues={
                    ':state': 'deleted',
                    ':version': new_version,
                    ':updated_at': timestamp,
                    ':change_entry': {change_entry}
                }
            )
            
            self.logger.info(f"Soft deleted item {item_id}")
            
        except ClientError as e:
            self.logger.error(f"Failed to delete item {item_id}: {str(e)}")
            raise
    
    def list_items(self, filters: Optional[Dict[str, Any]] = None, 
                  limit: int = 100) -> List[Dict[str, Any]]:
        """List items with optional filters"""
        try:
            scan_kwargs = {
                'Limit': limit,
                'FilterExpression': None
            }
            
            # Add state filter to exclude deleted items by default
            if filters is None:
                filters = {}
            
            if 'state' not in filters:
                from boto3.dynamodb.conditions import Attr
                scan_kwargs['FilterExpression'] = Attr('state').eq('active')
            
            # Add additional filters
            if filters:
                from boto3.dynamodb.conditions import Attr
                for key, value in filters.items():
                    if key == 'state':
                        scan_kwargs['FilterExpression'] = Attr(key).eq(value)
                    elif key == 'source':
                        filter_expr = Attr(key).eq(value)
                        if scan_kwargs['FilterExpression']:
                            filter_expr = scan_kwargs['FilterExpression'] & filter_expr
                        scan_kwargs['FilterExpression'] = filter_expr
            
            response = self.table.scan(**scan_kwargs)
            items = response.get('Items', [])
            
            # Handle pagination
            while 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
                response = self.table.scan(**scan_kwargs)
                items.extend(response.get('Items', []))
            
            self.logger.info(f"Listed {len(items)} items with filters {filters}")
            return items
            
        except ClientError as e:
            self.logger.error(f"Failed to list items: {str(e)}")
            raise
