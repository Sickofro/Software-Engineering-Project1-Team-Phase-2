# src/metrics/dataset_code_metric.py
"""
Dataset and code availability metric
"""

import requests
import re
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class DatasetCodeMetric:
    """Calculate dataset and code availability score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate dataset and code documentation score"""
        try:
            score = 0.0
            
            # Check for dataset information
            dataset_score = self._check_dataset_info(model_info)
            score += dataset_score * 0.6
            
            # Check for code availability
            code_score = self._check_code_availability(model_info)
            score += code_score * 0.4
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Dataset/code calculation failed: {str(e)}")
            return 0.5
    
    def _check_dataset_info(self, model_info: ModelInfo) -> float:
        """Check for dataset information"""
        try:
            score = 0.0
            
            # Check model-index for dataset information
            if model_info.model_index:
                for index_entry in model_info.model_index:
                    if 'datasets' in index_entry:
                        datasets = index_entry['datasets']
                        if isinstance(datasets, list) and len(datasets) > 0:
                            score += 0.5
                            break
            
            # Check README for dataset mentions
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code == 200:
                content = response.text.lower()
                
                dataset_terms = [
                    'dataset', 'training data', 'trained on', 'data source',
                    'corpus', 'collection', 'benchmark'
                ]
                
                found_terms = 0
                for term in dataset_terms:
                    if term in content:
                        found_terms += 1
                
                if found_terms >= 3:
                    score += 0.4
                elif found_terms >= 1:
                    score += 0.2
                
                # Look for specific dataset names or links
                if 'huggingface.co/datasets/' in content:
                    score += 0.3
                
                # Look for data size mentions
                data_size_pattern = r'\d+[kmb]?\s*(samples|examples|tokens|words|sentences)'
                if re.search(data_size_pattern, content, re.IGNORECASE):
                    score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Dataset info check failed: {str(e)}")
            return 0.4
    
    def _check_code_availability(self, model_info: ModelInfo) -> float:
        """Check for code availability and examples"""
        try:
            score = 0.0
            
            # Check for training/inference code files
            files_url = f"https://huggingface.co/api/models/{model_info.name}/tree/main"
            response = self.session.get(files_url, timeout=10)
            
            if response.status_code == 200:
                files_data = response.json()
                
                code_files = 0
                example_files = 0
                
                for item in files_data:
                    if 'path' in item:
                        filepath = item['path'].lower()
                        
                        if filepath.endswith('.py'):
                            code_files += 1
                            if any(word in filepath for word in ['train', 'inference', 'run', 'example', 'demo']):
                                example_files += 1
                        elif filepath.endswith('.ipynb'):
                            example_files += 1
                        elif filepath in ['training_args.json', 'run.sh', 'train.sh']:
                            code_files += 1
                
                if code_files > 0:
                    score += 0.3
                if example_files > 0:
                    score += 0.4
                if code_files >= 3:  # Multiple code files
                    score += 0.2
            
            # Check README for code examples
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            readme_response = self.session.get(readme_url, timeout=10)
            
            if readme_response.status_code == 200:
                content = readme_response.text
                
                # Look for code blocks
                code_blocks = content.count('```python') + content.count('```')
                if code_blocks >= 2:
                    score += 0.3
                elif code_blocks >= 1:
                    score += 0.2
                
                # Look for usage instructions
                if 'from transformers import' in content or 'import torch' in content:
                    score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Code availability check failed: {str(e)}")
            return 0.4