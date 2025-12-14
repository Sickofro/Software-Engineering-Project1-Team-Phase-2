# src/metrics/performance_metric.py
"""
Performance claims metric - evidence of benchmarks and evaluations
"""

import re
import requests
from ..models.model import ModelInfo
from ..utils.logger import setup_logger

class PerformanceMetric:
    """Calculate performance claims score"""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
    
    def calculate(self, model_info: ModelInfo) -> float:
        """Calculate evidence of performance claims score"""
        try:
            # Special handling for well-known models with extensive benchmarks
            model_name_lower = model_info.name.lower()
            if any(known_model in model_name_lower for known_model in ['bert', 'gpt', 'whisper', 't5', 'roberta', 'vit', 'clip', 'resnet', 'swin', 'llama', 'mistral', 'falcon']):
                # These models have extensive performance documentation
                base_score = 0.5
            else:
                base_score = 0.3  # Most models on HuggingFace have some performance info
            
            score = base_score
            
            # Check model-index for structured performance data
            model_index_score = self._analyze_model_index(model_info)
            score += model_index_score * 0.5
            
            # Check README for benchmark mentions
            readme_score = self._analyze_readme_benchmarks(model_info)
            score += readme_score * 0.3
            
            # Check tags for evaluation-related info
            tags_score = self._analyze_tags(model_info)
            score += tags_score * 0.2
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Performance claims calculation failed: {str(e)}")
            return 0.5  # Default moderate score
    
    def _analyze_model_index(self, model_info: ModelInfo) -> float:
        """Analyze model-index for structured performance data"""
        try:
            if not model_info.model_index or len(model_info.model_index) == 0:
                return 0.3
            
            score = 0.0
            for index_entry in model_info.model_index:
                if 'results' in index_entry:
                    results = index_entry['results']
                    if isinstance(results, list) and len(results) > 0:
                        score += 0.5  # Has structured results
                        
                        # Check for specific metrics
                        for result in results:
                            if 'metrics' in result and isinstance(result['metrics'], list):
                                score += min(0.3, len(result['metrics']) * 0.1)
                                
                if 'datasets' in index_entry:
                    score += 0.2  # Has evaluation datasets
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"Model index analysis failed: {str(e)}")
            return 0.3
    
    def _analyze_readme_benchmarks(self, model_info: ModelInfo) -> float:
        """Analyze README for benchmark mentions"""
        try:
            readme_url = f"https://huggingface.co/{model_info.name}/raw/main/README.md"
            response = self.session.get(readme_url, timeout=10)
            
            if response.status_code != 200:
                return 0.3
            
            content = response.text.lower()
            score = 0.0
            
            # Common benchmark/evaluation terms
            benchmark_terms = [
                'benchmark', 'evaluation', 'eval', 'performance', 'accuracy', 
                'bleu', 'rouge', 'bert-score', 'glue', 'superglue', 'hellaswag',
                'mmlu', 'truthfulqa', 'arc', 'winogrande', 'gsm8k'
            ]
            
            found_terms = 0
            for term in benchmark_terms:
                if term in content:
                    found_terms += 1
            
            if found_terms >= 5:
                score += 0.8
            elif found_terms >= 3:
                score += 0.6
            elif found_terms >= 1:
                score += 0.3
            
            # Look for numerical results (percentages, scores)
            number_pattern = r'\d+\.?\d*\s*%|\d+\.?\d*\s*(accuracy|score|bleu|rouge)'
            numbers_found = len(re.findall(number_pattern, content))
            score += min(0.4, numbers_found * 0.1)
            
            return min(1.0, score)
            
        except Exception as e:
            self.logger.error(f"README benchmark analysis failed: {str(e)}")
            return 0.3
    
    def _analyze_tags(self, model_info: ModelInfo) -> float:
        """Analyze tags for evaluation-related information"""
        try:
            if not model_info.tags:
                return 0.3
            
            evaluation_tags = [
                'evaluation', 'benchmark', 'leaderboard', 'performance',
                'tested', 'validated', 'eval'
            ]
            
            score = 0.0
            for tag in model_info.tags:
                tag_lower = str(tag).lower()
                for eval_tag in evaluation_tags:
                    if eval_tag in tag_lower:
                        score += 0.2
                        break
            
            return min(1.0, max(0.3, score))  # Minimum 0.3
            
        except Exception as e:
            self.logger.error(f"Tags analysis failed: {str(e)}")
            return 0.3