"""
Mock DynamoDB for local testing without Docker
This creates an in-memory database for development
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import re


class MockTable:
    """Mock DynamoDB table for local development"""
    
    def __init__(self, name: str):
        self.name = name
        self.items = {}
        self.indexes = {}
    
    def put_item(self, Item: Dict[str, Any]):
        """Add or update an item"""
        key = Item.get('id') or Item.get('artifact_id') or Item.get('name')
        self.items[key] = Item
    
    def get_item(self, Key: Dict[str, str]):
        """Get an item by key"""
        key_value = list(Key.values())[0]
        item = self.items.get(key_value)
        if item:
            return {'Item': item}
        return {}
    
    def update_item(self, Key: Dict[str, str], **kwargs):
        """Update an item"""
        key_value = list(Key.values())[0]
        if key_value in self.items:
            # Simple update - just update the timestamp
            self.items[key_value]['updated_at'] = datetime.utcnow().isoformat()
            return {'Attributes': self.items[key_value]}
        raise ValueError(f"Item not found: {key_value}")
    
    def delete_item(self, Key: Dict[str, str]):
        """Delete an item"""
        key_value = list(Key.values())[0]
        if key_value in self.items:
            del self.items[key_value]
    
    def scan(self, **kwargs):
        """Scan all items"""
        items = list(self.items.values())
        limit = kwargs.get('Limit', len(items))
        return {'Items': items[:limit]}
    
    def query(self, **kwargs):
        """Query items by index"""
        index_name = kwargs.get('IndexName')
        key_condition = kwargs.get('KeyConditionExpression')
        attr_values = kwargs.get('ExpressionAttributeValues', {})
        
        # Simple name-based filtering
        if ':name' in attr_values:
            search_name = attr_values[':name']
            results = [item for item in self.items.values() 
                      if item.get('name') == search_name]
            return {'Items': results}
        
        return {'Items': list(self.items.values())}
    
    def batch_writer(self):
        """Return a mock batch writer context"""
        return MockBatchWriter(self)


class MockBatchWriter:
    """Mock batch writer for bulk operations"""
    
    def __init__(self, table):
        self.table = table
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def delete_item(self, Key: Dict[str, str]):
        """Delete item in batch"""
        self.table.delete_item(Key)


class MockDynamoDB:
    """Mock DynamoDB resource"""
    
    def __init__(self):
        self.tables = {
            'Artifacts': MockTable('Artifacts'),
            'Ratings': MockTable('Ratings'),
            'Users': MockTable('Users'),
            'AuditLog': MockTable('AuditLog')
        }
    
    def Table(self, name: str):
        """Get a table by name"""
        if name not in self.tables:
            self.tables[name] = MockTable(name)
        return self.tables[name]


# Global mock instance
_mock_db = MockDynamoDB()


def get_mock_dynamodb():
    """Get the mock DynamoDB instance"""
    return _mock_db
