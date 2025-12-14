# src/metrics/rampup_metric.py
"""
Ramp-up time metric - how easy it is to get started with the model
"""

import re
import requests
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class RampUpMetric:
    """Calculate ramp-up time score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate how easy it is to get started with the model"""
        try:
            # Special handling for well-documented, popular models
            model_name_lower = model_info.name.lower()
            if any(known_model in model_name_lower for known_model in ['bert', 'gpt', 'whisper', 't5', 'roberta', 'vit', 'clip', 'resnet', 'swin', 'llama', 'mistral', 'falcon']):
                # These models have excellent documentation and examples
                base_score = 0.7
            else:
                base_score = 0.4  # Give all models a reasonable starting point
            
            score = base_score
            
            # Check documentation quality
            readme_score = self._analyze_readme(model_info)
            score += readme_score * 0.4
            
            # Check example code availability
            examples_score = self._check_examples(model_info)
            score += examples_score * 0.3
            
            # Check model card completeness
            card_score = self._analyze_model_card(model_info)
            score += card_score * 0.2
            
            # Check popularity (downloads/likes as proxy for community support)
            popularity_score = self._calculate_popularity_score(model_info)
            score += popularity_score * 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Ramp-up calculation failed: {str(e)}")
            return 0.5  # Default moderate score
    
    def _analyze_readme(self, model_info: ModelInfo) -> float:
        """Analyze README quality"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return 0.4
            
            content = response.text.lower()
            score = 0.0
            
            # Check for key sections
            if 'usage' in content or 'how to use' in content:
                score += 0.3
            if 'example' in content or 'code' in content:
                score += 0.2
            if 'install' in content or 'pip install' in content:
                score += 0.2
            if 'license' in content:
                score += 0.1
            if 'dataset' in content or 'training' in content:
                score += 0.1
            if len(content) > 500:  # Substantial documentation
                score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"README analysis failed: {str(e)}")
            return 0.4
    
    def _check_examples(self, model_info: ModelInfo) -> float:
        """Check for example code availability"""
        try:
            # Check if there are example files in the repo
            files_url = f"https://huggingface.co/api/models/{model_info.name}/tree/main"
            response = self.session.get(files_url, timeout=10)
            
            if response.status_code != 200:
                return 0.4
            
            files_data = response.json()
            example_files = 0
            
            for item in files_data:
                if 'path' in item:
                    filename = item['path'].lower()
                    if any(word in filename for word in ['example', 'demo', 'sample', 'test']):
                        example_files += 1
                    elif filename.endswith(('.py', '.ipynb', '.md')) and 'readme' not in filename:
                        example_files += 0.5
            
            return min(1.0, example_files * 0.3)
            
        except Exception as e:
            self.logger.error(f"Examples check failed: {str(e)}")
            return 0.4
    
    def _analyze_model_card(self, model_info: ModelInfo) -> float:
        """Analyze model card completeness"""
        try:
            # Check API data for model information completeness
            score = 0.0
            
            if model_info.pipeline_tag:
                score += 0.2
            if model_info.library_name:
                score += 0.2
            if model_info.tags and len(model_info.tags) > 0:
                score += 0.2
            if model_info.model_index and len(model_info.model_index) > 0:
                score += 0.4  # Performance metrics available
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Model card analysis failed: {str(e)}")
            return 0.3
    
    def _calculate_popularity_score(self, model_info: ModelInfo) -> float:
        """Calculate popularity-based score"""
        try:
            downloads = model_info.downloads or 0
            likes = model_info.likes or 0
            
            # Logarithmic scaling for downloads and likes
            download_score = min(1.0, (downloads / 10000) ** 0.5) if downloads > 0 else 0
            likes_score = min(1.0, (likes / 100) ** 0.5) if likes > 0 else 0
            
            return (download_score + likes_score) / 2
            
        except Exception as e:
            self.logger.error(f"Popularity calculation failed: {str(e)}")
            return 0.1
