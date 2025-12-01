# src/url_parser.py
"""
URL Parser module for identifying and parsing different types of URLs
"""

import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import requests
import json

from .models.model import ModelInfo, DatasetInfo, CodeInfo
from .utils.logger import setup_logger

class URLParser:
    """Parser for different types of URLs (Model, Dataset, Code)"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ACME-ML-Evaluator/1.0'
        })
    
    def identify_url_type(self, url: str) -> str:
        """Identify the type of URL"""
        url = url.lower().strip()
        
        if 'huggingface.co/datasets/' in url:
            return "DATASET"
        elif 'github.com/' in url:
            return "CODE" 
        elif 'huggingface.co/' in url:
            return "MODEL"
        else:
            # Default assumption
            return "MODEL"
    
    def parse_model_url(self, url: str) -> Optional[ModelInfo]:
        """Parse a Hugging Face model URL"""
        try:
            # Extract model name from URL
            if '/tree/main' in url:
                url = url.replace('/tree/main', '')
            
            # Extract model name from URL (handle both org/model and model formats)
            # Use a pattern that captures the full model path including slashes
            pattern = r'huggingface\.co/([^?]+)'
            match = re.search(pattern, url)
            if not match:
                self.logger.error(f"Could not parse model URL: {url}")
                return None
            
            model_id = match.group(1)
            
            # Fetch model information from HF API
            api_url = f"https://huggingface.co/api/models/{model_id}"
            
            try:
                response = self.session.get(api_url, timeout=30)
                if response.status_code == 200:
                    api_data = response.json()
                else:
                    api_data = {}
            except:
                api_data = {}
            
            # Create ModelInfo object
            model_info = ModelInfo(
                name=model_id,
                url=url,
                api_data=api_data,
                downloads=api_data.get('downloads', 0),
                likes=api_data.get('likes', 0),
                last_modified=api_data.get('lastModified', ''),
                tags=api_data.get('tags', []),
                pipeline_tag=api_data.get('pipeline_tag', ''),
                library_name=api_data.get('library_name', ''),
                model_index=api_data.get('model-index', [])
            )
            
            return model_info
            
        except Exception as e:
            self.logger.error(f"Failed to parse model URL {url}: {str(e)}")
            return None
    
    def parse_dataset_url(self, url: str) -> Optional[DatasetInfo]:
        """Parse a Hugging Face dataset URL"""
        try:
            # Extract dataset name from URL
            pattern = r'huggingface\.co/datasets/([^/]+/[^/?]+)'
            match = re.search(pattern, url)
            if not match:
                return None
            
            dataset_id = match.group(1)
            
            # Fetch dataset information from HF API
            api_url = f"https://huggingface.co/api/datasets/{dataset_id}"
            
            try:
                response = self.session.get(api_url, timeout=30)
                if response.status_code == 200:
                    api_data = response.json()
                else:
                    api_data = {}
            except:
                api_data = {}
            
            return DatasetInfo(
                name=dataset_id,
                url=url,
                api_data=api_data,
                downloads=api_data.get('downloads', 0),
                likes=api_data.get('likes', 0),
                tags=api_data.get('tags', [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse dataset URL {url}: {str(e)}")
            return None
    
    def parse_code_url(self, url: str) -> Optional[CodeInfo]:
        """Parse a GitHub code repository URL"""
        try:
            # Extract repo info from URL
            pattern = r'github\.com/([^/]+)/([^/?]+)'
            match = re.search(pattern, url)
            if not match:
                return None
            
            owner = match.group(1)
            repo = match.group(2)
            
            # Fetch repository information from GitHub API
            api_url = f"https://api.github.com/repos/{owner}/{repo}"
            
            try:
                response = self.session.get(api_url, timeout=30)
                if response.status_code == 200:
                    api_data = response.json()
                else:
                    api_data = {}
            except:
                api_data = {}
            
            return CodeInfo(
                name=f"{owner}/{repo}",
                url=url,
                api_data=api_data,
                stars=api_data.get('stargazers_count', 0),
                forks=api_data.get('forks_count', 0),
                language=api_data.get('language', ''),
                last_updated=api_data.get('updated_at', '')
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse code URL {url}: {str(e)}")
            return None
    
    def parse_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Parse any supported URL and return basic info as a dict
        This is a convenience method for the API endpoints
        """
        try:
            url_type = self.identify_url_type(url)
            
            if url_type == "MODEL":
                model_info = self.parse_model_url(url)
                if model_info:
                    return {
                        'name': model_info.name,
                        'type': 'model',
                        'url': url
                    }
            elif url_type == "DATASET":
                dataset_info = self.parse_dataset_url(url)
                if dataset_info:
                    return {
                        'name': dataset_info.name,
                        'type': 'dataset',
                        'url': url
                    }
            elif url_type == "CODE":
                code_info = self.parse_code_url(url)
                if code_info:
                    return {
                        'name': code_info.name,
                        'type': 'code',
                        'url': url
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to parse URL {url}: {str(e)}")
            return None