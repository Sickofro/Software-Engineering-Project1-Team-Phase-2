# src/aws/lambda_handler.py
"""
AWS Lambda handler for the ML Model Evaluator API
"""

import json
import os
from typing import Dict, Any
from ..url_parser import URLParser
from ..metrics.calculator import MetricsCalculator
from .dynamodb_service import DynamoDBService
from .s3_service import S3Service
from ..utils.logger import setup_logger

logger = setup_logger()

# Initialize services
dynamodb = DynamoDBService(
    table_name=os.environ.get('DYNAMODB_TABLE', 'ml-model-evaluator'),
    region=os.environ.get('AWS_REGION', 'us-east-1')
)
s3 = S3Service(
    bucket_name=os.environ.get('S3_BUCKET', 'ml-evaluator-artifacts'),
    region=os.environ.get('AWS_REGION', 'us-east-1')
)
url_parser = URLParser()
metrics_calculator = MetricsCalculator()

def lambda_handler(event, context):
    """
    Main Lambda handler for HTTP requests
    
    Expected event format (API Gateway proxy):
    {
        "httpMethod": "GET|POST|PUT|DELETE",
        "path": "/models|/health",
        "body": JSON string or null,
        "queryStringParameters": {...}
    }
    """
    try:
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Health check endpoint
        if path == '/health' and http_method == 'GET':
            return health_check()
        
        # CRUD endpoints
        if path.startswith('/models'):
            if http_method == 'GET':
                return get_models(event)
            elif http_method == 'POST':
                return create_model(event)
            elif http_method == 'PUT':
                return update_model(event)
            elif http_method == 'DELETE':
                return delete_model(event)
        
        # Evaluate endpoint
        if path == '/evaluate' and http_method == 'POST':
            return evaluate_model(event)
        
        return error_response(404, "Not Found")
        
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return error_response(500, "Internal Server Error")

def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    return response(200, {
        'status': 'healthy',
        'service': 'ml-model-evaluator',
        'version': '2.0'
    })

def create_model(event) -> Dict[str, Any]:
    """Create a new model record"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        name = body.get('name')
        source = body.get('source')
        license = body.get('license')
        metadata = body.get('metadata', {})
        risk_notes = body.get('risk_notes', '')
        
        if not all([name, source, license]):
            return error_response(400, "Missing required fields: name, source, license")
        
        item = dynamodb.create_item(
            name=name,
            source=source,
            license=license,
            metadata=metadata,
            risk_notes=risk_notes
        )
        
        return response(201, {
            'success': True,
            'item': item
        })
        
    except json.JSONDecodeError:
        return error_response(400, "Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Failed to create model: {str(e)}")
        return error_response(500, "Failed to create model")

def get_models(event) -> Dict[str, Any]:
    """Get model records"""
    try:
        query_params = event.get('queryStringParameters') or {}
        
        # Check if specific model ID is requested
        model_id = query_params.get('id')
        if model_id:
            item = dynamodb.read_item(model_id)
            if item:
                return response(200, {'item': item})
            else:
                return error_response(404, "Model not found")
        
        # List all models with optional filters
        filters = {}
        if 'source' in query_params:
            filters['source'] = query_params['source']
        if 'state' in query_params:
            filters['state'] = query_params['state']
        
        items = dynamodb.list_items(filters=filters, limit=100)
        return response(200, {
            'items': items,
            'count': len(items)
        })
        
    except Exception as e:
        logger.error(f"Failed to get models: {str(e)}")
        return error_response(500, "Failed to retrieve models")

def update_model(event) -> Dict[str, Any]:
    """Update a model record"""
    try:
        body = json.loads(event.get('body', '{}'))
        model_id = body.get('id')
        
        if not model_id:
            return error_response(400, "Missing required field: id")
        
        updates = {k: v for k, v in body.items() if k not in ['id']}
        
        if not updates:
            return error_response(400, "No fields to update")
        
        item = dynamodb.update_item(
            item_id=model_id,
            updates=updates,
            changed_by=body.get('changed_by', 'api-user')
        )
        
        return response(200, {
            'success': True,
            'item': item
        })
        
    except json.JSONDecodeError:
        return error_response(400, "Invalid JSON in request body")
    except ValueError as e:
        return error_response(404, str(e))
    except Exception as e:
        logger.error(f"Failed to update model: {str(e)}")
        return error_response(500, "Failed to update model")

def delete_model(event) -> Dict[str, Any]:
    """Soft delete a model record"""
    try:
        body = json.loads(event.get('body', '{}'))
        model_id = body.get('id')
        
        if not model_id:
            return error_response(400, "Missing required field: id")
        
        dynamodb.delete_item(
            item_id=model_id,
            changed_by=body.get('changed_by', 'api-user')
        )
        
        return response(200, {
            'success': True,
            'message': f"Model {model_id} deleted"
        })
        
    except json.JSONDecodeError:
        return error_response(400, "Invalid JSON in request body")
    except ValueError as e:
        return error_response(404, str(e))
    except Exception as e:
        logger.error(f"Failed to delete model: {str(e)}")
        return error_response(500, "Failed to delete model")

def evaluate_model(event) -> Dict[str, Any]:
    """Evaluate a model from URL"""
    try:
        body = json.loads(event.get('body', '{}'))
        url = body.get('url')
        
        if not url:
            return error_response(400, "Missing required field: url")
        
        # Identify URL type and parse
        url_type = url_parser.identify_url_type(url)
        
        if url_type == "MODEL":
            model_info = url_parser.parse_model_url(url)
            if not model_info:
                return error_response(400, "Failed to parse model URL")
            
            # Calculate metrics
            metrics = metrics_calculator.calculate_all_metrics(model_info)
            
            # Store result in S3
            result_key = f"evaluations/{model_info.name.replace('/', '-')}.json"
            s3.upload_bytes(
                data=json.dumps(metrics).encode(),
                key=result_key,
                metadata={'model_name': model_info.name}
            )
            
            return response(200, {
                'success': True,
                'metrics': metrics,
                'stored_at': result_key
            })
        else:
            return error_response(400, f"URL type {url_type} not yet supported for evaluation")
        
    except json.JSONDecodeError:
        return error_response(400, "Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Failed to evaluate model: {str(e)}")
        return error_response(500, "Failed to evaluate model")

def response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format a response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Format an error response"""
    return response(status_code, {
        'success': False,
        'error': message
    })
