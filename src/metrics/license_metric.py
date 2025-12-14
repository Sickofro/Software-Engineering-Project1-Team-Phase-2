
# src/metrics/license_metric.py
"""
License metric calculation
"""

import re
import requests
from typing import Dict, Any
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class LicenseMetric:
    """Calculate license score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
        
        # License compatibility with LGPLv2.1
        self.license_scores = {
            'apache-2.0': 0.9,  # Apache 2.0 is fully compatible
            'mit': 0.9,  # MIT is fully compatible
            'bsd-3-clause': 1.0,  # BSD is fully compatible
            'bsd-2-clause': 1.0,  # BSD is fully compatible
            'lgpl-2.1': 1.0,
            'lgpl-3.0': 0.8,
            'gpl-2.0': 0.3,  # Less compatible
            'gpl-3.0': 0.3,  # Less compatible
            'cc-by-4.0': 0.7,
            'cc-by-sa-4.0': 0.6,
            'unknown': 0.5,
            'other': 0.5
        }
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate license compatibility score"""
        try:
            # Try to get license from API data first
            license_info = None
            if 'license' in model_info.api_data:
                license_info = model_info.api_data['license']
            
            if not license_info:
                # Fallback: fetch README and parse license
                license_info = self._parse_license_from_readme(model_info)
            
            if not license_info:
                return 0.5  # Unknown license - give moderate score
            
            # Normalize license string
            license_key = str(license_info).lower().strip()
            
            # Check against known licenses
            for known_license, score in self.license_scores.items():
                if known_license in license_key:
                    return score
            
            # Check for permissive patterns
            if any(word in license_key for word in ['apache', 'mit', 'bsd']):
                return 0.9
            elif any(word in license_key for word in ['cc', 'creative']):
                return 0.7
            elif 'lgpl' in license_key:
                return 0.9
            elif 'gpl' in license_key:
                return 0.3
            else:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"License calculation failed: {str(e)}")
            return 0.5
    
    def _parse_license_from_readme(self, model_info: ModelInfo) -> str:
        """Parse license from README file"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            content = response.text
            
            # Look for license section
            license_match = re.search(r'#+\s*License\s*\n(.*?)(?=\n#|\n\n|\Z)', content, re.IGNORECASE | re.DOTALL)
            if license_match:
                return license_match.group(1).strip()
            
            # Look for license mentions
            license_pattern = r'license[:\s]+([^\n]+)'
            match = re.search(license_pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            
            return None
            
        except Exception as e:
            self.logger.error(f"README parsing failed: {str(e)}")
            return None
