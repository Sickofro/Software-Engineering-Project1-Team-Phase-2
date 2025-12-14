
# src/metrics/size_metric.py
"""
Size metric calculation for different hardware platforms
"""

import requests
import json
from typing import Dict, Any
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class SizeMetric:
    """Calculate size compatibility score for different hardware"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
        
        # Hardware constraints (in GB)
        self.hardware_limits = {
            'raspberry_pi': 1.0,    # 1GB model constraint
            'jetson_nano': 4.0,     # 4GB RAM typical
            'desktop_pc': 16.0,     # 16GB RAM typical
            'aws_server': 64.0      # Large instance
        }
    
    def calculate(self, model_info: ModelInfo) -> Dict[str, float]:
        """Calculate size scores for different hardware platforms"""
        try:
            model_size_gb = self._estimate_model_size(model_info)
            
            scores = {}
            for hardware, limit in self.hardware_limits.items():
                if model_size_gb <= limit * 0.5:  # Comfortably fits
                    scores[hardware] = 1.0
                elif model_size_gb <= limit * 0.8:  # Fits with some room
                    scores[hardware] = 0.9
                elif model_size_gb <= limit:  # Just fits
                    scores[hardware] = 0.8
                elif model_size_gb <= limit * 1.5:  # Might work with optimizations
                    scores[hardware] = 0.6
                elif model_size_gb <= limit * 2.0:  # Could work with quantization
                    scores[hardware] = 0.5
                elif model_size_gb <= limit * 3.0:  # Needs significant optimization
                    scores[hardware] = 0.4
                else:  # Too large but still give some score
                    scores[hardware] = 0.3
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Size calculation failed: {str(e)}")
            return {hw: 0.7 for hw in self.hardware_limits.keys()}
    
    def _estimate_model_size(self, model_info: ModelInfo) -> float:
        """Estimate model size in GB"""
        try:
            # Try to get size from model files
            files_url = f"https://huggingface.co/api/models/{model_info.name}/tree/main"
            response = self.session.get(files_url, timeout=10)
            
            total_size = 0
            if response.status_code == 200:
                files_data = response.json()
                for item in files_data:
                    if 'size' in item:
                        total_size += item['size']
            
            if total_size > 0:
                return total_size / (1024 ** 3)  # Convert to GB
            
            # Fallback: estimate from model name/tags
            model_name_lower = model_info.name.lower()
            if any(size in model_name_lower for size in ['7b', '7-b']):
                return 13.0  # ~13GB for 7B models
            elif any(size in model_name_lower for size in ['13b', '13-b']):
                return 26.0  # ~26GB for 13B models
            elif any(size in model_name_lower for size in ['70b', '70-b']):
                return 140.0  # ~140GB for 70B models
            elif any(size in model_name_lower for size in ['3b', '3-b']):
                return 6.0   # ~6GB for 3B models
            elif any(size in model_name_lower for size in ['1b', '1-b']):
                return 2.0   # ~2GB for 1B models
            elif 'small' in model_name_lower:
                return 0.5   # Small models
            elif 'large' in model_name_lower:
                return 5.0   # Large models
            else:
                return 2.0   # Default assumption
                
        except Exception as e:
            self.logger.error(f"Size estimation failed: {str(e)}")
            return 2.0  # Default fallback