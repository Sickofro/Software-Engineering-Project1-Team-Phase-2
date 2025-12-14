# src/metrics/dataset_quality_metric.py
"""
Dataset quality metric
"""

import requests
import re
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class DatasetQualityMetric:
    """Calculate dataset quality score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate dataset quality score"""
        try:
            # Start with a higher base score
            score = 0.4
            
            # Check for dataset documentation
            documentation_score = self._check_dataset_documentation(model_info)
            score += documentation_score * 0.3
            
            # Check for data preprocessing information
            preprocessing_score = self._check_preprocessing_info(model_info)
            score += preprocessing_score * 0.2
            
            # Check for known high-quality datasets
            quality_datasets_score = self._check_known_datasets(model_info)
            score += quality_datasets_score * 0.2
            
            return min(1.0, max(0.5, score))  # Minimum 0.5
            
        except Exception as e:
            self.logger.error(f"Dataset quality calculation failed: {str(e)}")
            return 0.6
    
    def _check_dataset_documentation(self, model_info: ModelInfo) -> float:
        """Check quality of dataset documentation"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return 0.4
            
            content = response.text.lower()
            score = 0.0
            
            # Look for detailed dataset information
            dataset_quality_terms = [
                'data source', 'data collection', 'data cleaning', 'preprocessing',
                'filtering', 'deduplication', 'quality control', 'curation',
                'annotation', 'labeling', 'validation'
            ]
            
            found_terms = 0
            for term in dataset_quality_terms:
                if term in content:
                    found_terms += 1
            
            score += min(0.6, found_terms * 0.1)
            
            # Check for specific dataset size information
            if re.search(r'\d+[kmb]?\s*(tokens|words|samples|examples)', content):
                score += 0.2
            
            # Check for data composition details
            if any(term in content for term in ['composition', 'distribution', 'breakdown', 'statistics']):
                score += 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Dataset documentation check failed: {str(e)}")
            return 0.4
    
    def _check_preprocessing_info(self, model_info: ModelInfo) -> float:
        """Check for data preprocessing information"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return 0.4
            
            content = response.text.lower()
            score = 0.0
            
            preprocessing_terms = [
                'tokenization', 'normalization', 'cleaning', 'filtering',
                'preprocessing', 'preparation', 'augmentation', 'transformation'
            ]
            
            found_terms = 0
            for term in preprocessing_terms:
                if term in content:
                    found_terms += 1
            
            score += min(0.8, found_terms * 0.15)
            
            # Check for specific preprocessing tools/methods
            if any(tool in content for tool in ['spacy', 'nltk', 'tokenizer', 'bpe', 'sentencepiece']):
                score += 0.2
            
            return max(0.4, min(1.0, score))  # Minimum 0.4
            
        except Exception as e:
            self.logger.error(f"Preprocessing info check failed: {str(e)}")
            return 0.4
    
    def _check_known_datasets(self, model_info: ModelInfo) -> float:
        """Check if trained on known high-quality datasets"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return 0.3
            
            content = response.text.lower()
            
            # Known high-quality datasets
            quality_datasets = {
                'common crawl': 0.7,
                'c4': 0.8,
                'pile': 0.8,
                'openwebtext': 0.7,
                'wikipedia': 0.9,
                'books3': 0.6,
                'arxiv': 0.8,
                'pubmed': 0.8,
                'github': 0.7,
                'stackexchange': 0.7,
                'refinedweb': 0.8,
                'dolma': 0.8,
                'redpajama': 0.7
            }
            
            max_score = 0.0
            for dataset, score in quality_datasets.items():
                if dataset in content:
                    max_score = max(max_score, score)
            
            if max_score == 0.0:
                # Check for general indicators of quality
                if any(term in content for term in ['curated', 'filtered', 'high-quality', 'clean']):
                    max_score = 0.5
                else:
                    max_score = 0.3  # Default moderate score
            
            return max_score
            
        except Exception as e:
            self.logger.error(f"Known datasets check failed: {str(e)}")
            return 0.3