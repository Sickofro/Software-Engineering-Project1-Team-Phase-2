# src/metrics/busfactor_metric.py
"""
Bus factor metric - measuring knowledge concentration/maintainer responsiveness
"""

import requests
import json
from datetime import datetime, timedelta
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class BusFactorMetric:
    """Calculate bus factor score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate bus factor (higher = safer/better maintained)"""
        try:
            # Special handling for well-known, well-maintained models
            model_name_lower = model_info.name.lower()
            if any(known_model in model_name_lower for known_model in ['bert', 'gpt', 'whisper', 't5', 'roberta', 'vit', 'clip', 'resnet', 'swin', 'llama', 'mistral', 'falcon']):
                # These models are well-established and maintained
                base_score = 0.6
            else:
                base_score = 0.4  # Most HuggingFace models have decent maintenance
            
            score = base_score
            
            # Check recent activity
            activity_score = self._check_recent_activity(model_info)
            score += activity_score * 0.4
            
            # Check maintainer info
            maintainer_score = self._analyze_maintainers(model_info)
            score += maintainer_score * 0.3
            
            # Check community engagement
            community_score = self._assess_community(model_info)
            score += community_score * 0.3
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Bus factor calculation failed: {str(e)}")
            return 0.5  # Default moderate score
    
    def _check_recent_activity(self, model_info: ModelInfo) -> float:
        """Check for recent activity/updates"""
        try:
            if not model_info.last_modified:
                return 0.5
            
            # Parse last modified date
            try:
                last_mod = datetime.fromisoformat(model_info.last_modified.replace('Z', '+00:00'))
                now = datetime.now(last_mod.tzinfo)
                
                days_old = (now - last_mod).days
                
                if days_old <= 30:      # Very recent
                    return 1.0
                elif days_old <= 90:    # Recent
                    return 0.8
                elif days_old <= 180:   # Somewhat recent
                    return 0.6
                elif days_old <= 365:   # Within a year
                    return 0.4
                else:                   # Old
                    return 0.2
                    
            except:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Activity check failed: {str(e)}")
            return 0.5
    
    def _analyze_maintainers(self, model_info: ModelInfo) -> float:
        """Analyze maintainer information"""
        try:
            # Extract organization/user from model name
            parts = model_info.name.split('/')
            if len(parts) < 2:
                return 0.5
            
            org_name = parts[0]
            score = 0.0
            
            # Well-known organizations get higher scores
            known_orgs = {
                'openai': 0.9,
                'google': 0.9,
                'microsoft': 0.9,
                'meta-llama': 0.9,
                'anthropic': 0.9,
                'huggingface': 0.8,
                'facebook': 0.8,
                'mistralai': 0.8,
                'nvidia': 0.8,
                'stabilityai': 0.7
            }
            
            org_lower = org_name.lower()
            for known_org, org_score in known_orgs.items():
                if known_org in org_lower:
                    score = max(score, org_score)
                    break
            
            if score == 0.0:
                # Unknown organization, moderate score
                score = 0.5
            
            return score
            
        except Exception as e:
            self.logger.error(f"Maintainer analysis failed: {str(e)}")
            return 0.4
    
    def _assess_community(self, model_info: ModelInfo) -> float:
        """Assess community engagement"""
        try:
            likes = model_info.likes or 0
            downloads = model_info.downloads or 0
            
            # Community score based on engagement
            if likes > 1000 or downloads > 100000:
                return 1.0
            elif likes > 100 or downloads > 10000:
                return 0.8
            elif likes > 10 or downloads > 1000:
                return 0.6
            elif likes > 0 or downloads > 0:
                return 0.4
            else:
                return 0.4
                
        except Exception as e:
            self.logger.error(f"Community assessment failed: {str(e)}")
            return 0.4