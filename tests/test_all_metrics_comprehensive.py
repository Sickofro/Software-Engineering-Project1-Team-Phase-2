# tests/test_all_metrics_comprehensive.py
"""
Comprehensive tests for all metrics to ensure they work correctly
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.models.model import ModelInfo
from src.metrics.license_metric import LicenseMetric
from src.metrics.size_metric import SizeMetric
from src.metrics.busfactor_metric import BusFactorMetric
from src.metrics.performance_metric import PerformanceMetric
from src.metrics.dataset_code_metric import DatasetCodeMetric
from src.metrics.dataset_quality_metric import DatasetQualityMetric
from src.metrics.code_quality_metric import CodeQualityMetric
from src.metrics.rampup_metric import RampUpMetric
from src.metrics.calculator import MetricsCalculator


class TestLicenseMetricComprehensive:
    """Comprehensive tests for License Metric"""
    
    def test_license_metric_apache_license(self):
        """Test Apache license gets high score"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/apache-model",
            url="https://huggingface.co/test/apache-model",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
    
        result = metric.calculate(model_info)
        assert result == 1.0, f"Apache license should score 1.0, got {result}"

    def test_license_metric_mit_license(self):
        """Test MIT license gets high score"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/mit-model",
            url="https://huggingface.co/test/mit-model",
            api_data={'license': 'mit'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 1.0, f"MIT license should score 1.0, got {result}"
    
    def test_license_metric_gpl_license(self):
        """Test GPL license gets low score"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/gpl-model",
            url="https://huggingface.co/test/gpl-model",
            api_data={'license': 'gpl-3.0'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.3, f"GPL license should score 0.3, got {result}"
    
    def test_license_metric_unknown_license(self):
        """Test unknown license gets low score"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/unknown-model",
            url="https://huggingface.co/test/unknown-model",
            api_data={'license': 'unknown'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.1, f"Unknown license should score 0.1, got {result}"
    
    @patch('src.metrics.license_metric.requests.Session.get')
    def test_license_metric_readme_parsing(self, mock_get):
        """Test license parsing from README"""
        metric = LicenseMetric()
        
        # Mock README with Apache license
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Name
        
        ## License
        This model is licensed under the Apache License 2.0
        """
        mock_get.return_value = mock_response
        
        model_info = ModelInfo(
            name="test/readme-model",
            url="https://huggingface.co/test/readme-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.9, f"README Apache license should score 0.9, got {result}"


class TestSizeMetricComprehensive:
    """Comprehensive tests for Size Metric"""
    
    def test_size_metric_small_model(self):
        """Test small model gets good scores"""
        metric = SizeMetric()
        model_info = ModelInfo(
            name="test/small-model",
            url="https://huggingface.co/test/small-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        with patch.object(metric, '_estimate_model_size', return_value=0.5):
            result = metric.calculate(model_info)
            
            assert isinstance(result, dict)
            assert 'raspberry_pi' in result
            assert 'jetson_nano' in result
            assert 'desktop_pc' in result
            assert 'aws_server' in result
            
            # Small model should work on all platforms
            assert result['raspberry_pi'] == 1.0
            assert result['jetson_nano'] == 1.0
            assert result['desktop_pc'] == 1.0
            assert result['aws_server'] == 1.0
    
    def test_size_metric_large_model(self):
        """Test large model gets appropriate scores"""
        metric = SizeMetric()
        model_info = ModelInfo(
            name="test/7b-model",
            url="https://huggingface.co/test/7b-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        with patch.object(metric, '_estimate_model_size', return_value=13.0):
            result = metric.calculate(model_info)
            
            # Large model should not work on Raspberry Pi
            assert result['raspberry_pi'] == 0.0
            # Should work on larger platforms (13GB fits in 16GB desktop)
            assert result['desktop_pc'] >= 0.6  # Should be at least 0.6 for 13GB in 16GB
            assert result['aws_server'] == 1.0
    
    def test_size_metric_estimation_from_name(self):
        """Test size estimation from model name"""
        metric = SizeMetric()
        model_info = ModelInfo(
            name="test/7b-model",
            url="https://huggingface.co/test/7b-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        with patch('src.metrics.size_metric.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response
            
            size = metric._estimate_model_size(model_info)
            assert size == 13.0  # 7B model estimated size


class TestBusFactorMetricComprehensive:
    """Comprehensive tests for Bus Factor Metric"""
    
    def test_bus_factor_recent_activity(self):
        """Test recent activity gets high score"""
        metric = BusFactorMetric()
        model_info = ModelInfo(
            name="google/recent-model",
            url="https://huggingface.co/google/recent-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=1000,
            downloads=50000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Recent activity should get good score
        assert result > 0.5
    
    def test_bus_factor_old_activity(self):
        """Test old activity gets lower score"""
        metric = BusFactorMetric()
        model_info = ModelInfo(
            name="test/old-model",
            url="https://huggingface.co/test/old-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=10,
            downloads=100,
            last_modified="2020-01-01T00:00:00Z"
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Old activity should get lower score
        assert result < 0.8
    
    def test_bus_factor_known_organization(self):
        """Test known organization gets good score"""
        metric = BusFactorMetric()
        model_info = ModelInfo(
            name="google/test-model",
            url="https://huggingface.co/google/test-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=100,
            downloads=1000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Known organization should get good score
        assert result > 0.5


class TestPerformanceMetricComprehensive:
    """Comprehensive tests for Performance Metric"""
    
    def test_performance_with_model_index(self):
        """Test performance with model index data"""
        metric = PerformanceMetric()
        model_info = ModelInfo(
            name="test/benchmarked-model",
            url="https://huggingface.co/test/benchmarked-model",
            api_data={},
            model_index=[{
                'results': [{
                    'metrics': ['accuracy', 'bleu', 'rouge']
                }]
            }],
            tags=['evaluation', 'benchmark'],
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with structured results should get good score
        assert result > 0.3
    
    @patch('src.metrics.performance_metric.requests.Session.get')
    def test_performance_with_readme_benchmarks(self, mock_get):
        """Test performance with README benchmarks"""
        metric = PerformanceMetric()
        
        # Mock README with benchmark information
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Performance
        
        ## Benchmarks
        - GLUE: 85.2%
        - SuperGLUE: 78.5%
        - BLEU: 45.6
        - ROUGE: 52.3
        """
        mock_get.return_value = mock_response
        
        model_info = ModelInfo(
            name="test/benchmarked-model",
            url="https://huggingface.co/test/benchmarked-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with benchmark data should get good score
        assert result > 0.2
    
    def test_performance_with_evaluation_tags(self):
        """Test performance with evaluation tags"""
        metric = PerformanceMetric()
        model_info = ModelInfo(
            name="test/evaluated-model",
            url="https://huggingface.co/test/evaluated-model",
            api_data={},
            model_index=None,
            tags=['evaluation', 'benchmark', 'performance'],
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with evaluation tags should get moderate score
        assert result > 0.1


class TestDatasetCodeMetricComprehensive:
    """Comprehensive tests for Dataset Code Metric"""
    
    def test_dataset_code_with_model_index(self):
        """Test dataset code with model index"""
        metric = DatasetCodeMetric()
        model_info = ModelInfo(
            name="test/documented-model",
            url="https://huggingface.co/test/documented-model",
            api_data={},
            model_index=[{
                'datasets': ['dataset1', 'dataset2']
            }],
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with dataset info should get good score
        assert result >= 0.3
    
    @patch('src.metrics.dataset_code_metric.requests.Session.get')
    def test_dataset_code_with_readme(self, mock_get):
        """Test dataset code with README documentation"""
        metric = DatasetCodeMetric()

        # Mock README with dataset and code information
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Documentation

        ## Dataset
        This model was trained on a large dataset of 1M samples.
        The training data was collected from various sources.

        ## Code Example
        ```python
        from transformers import AutoModel
        model = AutoModel.from_pretrained('test/model')
        ```
        """
        mock_get.return_value = mock_response

        model_info = ModelInfo(
            name="test/documented-model",
            url="https://huggingface.co/test/documented-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )

        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with good documentation should get good score
        assert result >= 0.4


class TestDatasetQualityMetricComprehensive:
    """Comprehensive tests for Dataset Quality Metric"""
    
    @patch('src.metrics.dataset_quality_metric.requests.Session.get')
    def test_dataset_quality_with_readme(self, mock_get):
        """Test dataset quality with README"""
        metric = DatasetQualityMetric()
        
        # Mock README with quality information
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Documentation
        
        ## Dataset Quality
        The model was trained on high-quality, curated data.
        Data preprocessing included cleaning, filtering, and deduplication.
        The dataset contains 1M samples with quality control measures.
        """
        mock_get.return_value = mock_response
        
        model_info = ModelInfo(
            name="test/quality-model",
            url="https://huggingface.co/test/quality-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with quality documentation should get good score
        assert result > 0.4


class TestCodeQualityMetricComprehensive:
    """Comprehensive tests for Code Quality Metric"""
    
    @patch('src.metrics.code_quality_metric.requests.Session.get')
    def test_code_quality_with_files(self, mock_get):
        """Test code quality with file analysis"""
        metric = CodeQualityMetric()
        
        # Mock file listing response
        files_response = Mock()
        files_response.status_code = 200
        files_response.json.return_value = [
            {'path': 'requirements.txt'},
            {'path': 'config.json'},
            {'path': 'train.py'},
            {'path': 'inference.py'},
            {'path': 'README.md'}
        ]
        
        # Mock file content response
        file_response = Mock()
        file_response.status_code = 200
        file_response.text = '''
        def train_model():
            """
            Train the model with proper documentation.
            """
            # This is a well-documented function
            pass
        '''
        
        mock_get.side_effect = [files_response, file_response]
        
        model_info = ModelInfo(
            name="test/quality-model",
            url="https://huggingface.co/test/quality-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with good file structure should get good score
        assert result > 0.3


class TestRampUpMetricComprehensive:
    """Comprehensive tests for Ramp Up Metric"""
    
    @patch('src.metrics.rampup_metric.requests.Session.get')
    def test_rampup_with_readme(self, mock_get):
        """Test ramp up with README"""
        metric = RampUpMetric()

        # Mock README with usage information
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Usage

        ## Quick Start
        ```python
        from transformers import AutoModel
        model = AutoModel.from_pretrained('test/model')
        ```

        ## Examples
        See the examples/ directory for usage examples.
        """
        mock_get.return_value = mock_response

        model_info = ModelInfo(
            name="test/rampup-model",
            url="https://huggingface.co/test/rampup-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=100,
            downloads=1000,
            last_modified=None
        )

        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
        # Model with good documentation should get good score
        assert result >= 0.3


class TestMetricsCalculatorComprehensive:
    """Comprehensive tests for Metrics Calculator"""
    
    def test_calculate_all_metrics_integration(self):
        """Test full metrics calculation integration"""
        calculator = MetricsCalculator()
        
        model_info = ModelInfo(
            name="test/integration-model",
            url="https://huggingface.co/test/integration-model",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=['text-generation'],
            likes=100,
            downloads=1000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        # Mock all metric calculations to avoid API calls
        with patch.object(calculator.license_metric, 'calculate', return_value=0.9), \
             patch.object(calculator.size_metric, 'calculate', return_value={'raspberry_pi': 0.5, 'jetson_nano': 0.8, 'desktop_pc': 1.0, 'aws_server': 1.0}), \
             patch.object(calculator.rampup_metric, 'calculate', return_value=0.7), \
             patch.object(calculator.busfactor_metric, 'calculate', return_value=0.6), \
             patch.object(calculator.performance_metric, 'calculate', return_value=0.5), \
             patch.object(calculator.dataset_code_metric, 'calculate', return_value=0.4), \
             patch.object(calculator.dataset_quality_metric, 'calculate', return_value=0.3), \
             patch.object(calculator.code_quality_metric, 'calculate', return_value=0.8):
            
            result = calculator.calculate_all_metrics(model_info)
            
            # Verify all required fields are present
            required_fields = [
                'name', 'category', 'net_score', 'net_score_latency',
                'ramp_up_time', 'ramp_up_time_latency',
                'bus_factor', 'bus_factor_latency',
                'performance_claims', 'performance_claims_latency',
                'license', 'license_latency',
                'size_score', 'size_score_latency',
                'dataset_and_code_score', 'dataset_and_code_score_latency',
                'dataset_quality', 'dataset_quality_latency',
                'code_quality', 'code_quality_latency'
            ]
            
            for field in required_fields:
                assert field in result, f"Missing required field: {field}"
            
            # Verify data types and ranges
            assert result['name'] == "test/integration-model"
            assert result['category'] == "MODEL"
            assert 0.0 <= result['net_score'] <= 1.0
            assert isinstance(result['net_score_latency'], int)
            assert result['net_score_latency'] >= 0
            
            # Verify size_score is a dict with hardware mappings
            assert isinstance(result['size_score'], dict)
            assert 'raspberry_pi' in result['size_score']
            assert 'jetson_nano' in result['size_score']
            assert 'desktop_pc' in result['size_score']
            assert 'aws_server' in result['size_score']
            
            # Verify all scores are in valid range
            score_fields = ['ramp_up_time', 'bus_factor', 'performance_claims', 
                          'license', 'dataset_and_code_score', 'dataset_quality', 'code_quality']
            for field in score_fields:
                assert 0.0 <= result[field] <= 1.0, f"Invalid score for {field}: {result[field]}"
            
            # Verify all latencies are non-negative integers
            latency_fields = [f for f in result.keys() if f.endswith('_latency')]
            for field in latency_fields:
                assert isinstance(result[field], int), f"Invalid latency type for {field}: {type(result[field])}"
                assert result[field] >= 0, f"Negative latency for {field}: {result[field]}"
    
    def test_net_score_calculation(self):
        """Test net score calculation"""
        calculator = MetricsCalculator()
        
        metrics = {
            'license': 0.9,
            'ramp_up_time': 0.7,
            'bus_factor': 0.6,
            'performance_claims': 0.5,
            'size_score': {'raspberry_pi': 0.5, 'jetson_nano': 0.8, 'desktop_pc': 1.0, 'aws_server': 1.0},
            'dataset_and_code_score': 0.4,
            'dataset_quality': 0.3,
            'code_quality': 0.8
        }
        
        net_score = calculator._calculate_net_score(metrics)
        assert 0.0 <= net_score <= 1.0
        # Should be a weighted average of all metrics
        assert net_score > 0.0
        assert net_score < 1.0


class TestEndToEndComprehensive:
    """End-to-end comprehensive tests"""
    
    def test_full_pipeline_with_real_model(self):
        """Test full pipeline with a real model (if API is available)"""
        calculator = MetricsCalculator()
        
        model_info = ModelInfo(
            name="google/gemma-3-270m",
            url="https://huggingface.co/google/gemma-3-270m",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=['text-generation'],
            likes=500,
            downloads=10000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        # This will make actual API calls
        result = calculator.calculate_all_metrics(model_info)
        
        # Verify the result structure
        assert isinstance(result, dict)
        assert 'name' in result
        assert 'net_score' in result
        
        # Verify all required fields are present
        required_fields = [
            'name', 'category', 'net_score', 'net_score_latency',
            'ramp_up_time', 'ramp_up_time_latency',
            'bus_factor', 'bus_factor_latency',
            'performance_claims', 'performance_claims_latency',
            'license', 'license_latency',
            'size_score', 'size_score_latency',
            'dataset_and_code_score', 'dataset_and_code_score_latency',
            'dataset_quality', 'dataset_quality_latency',
            'code_quality', 'code_quality_latency'
        ]
        
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"
        
        # Verify data types and ranges
        assert result['name'] == "google/gemma-3-270m"
        assert result['category'] == "MODEL"
        assert 0.0 <= result['net_score'] <= 1.0
        
        # Verify size_score structure
        assert isinstance(result['size_score'], dict)
        assert 'raspberry_pi' in result['size_score']
        assert 'jetson_nano' in result['size_score']
        assert 'desktop_pc' in result['size_score']
        assert 'aws_server' in result['size_score']
        
        # Verify all scores are in valid range
        score_fields = ['ramp_up_time', 'bus_factor', 'performance_claims', 
                      'license', 'dataset_and_code_score', 'dataset_quality', 'code_quality']
        for field in score_fields:
            assert 0.0 <= result[field] <= 1.0, f"Invalid score for {field}: {result[field]}"
        
        # Verify all latencies are non-negative integers
        latency_fields = [f for f in result.keys() if f.endswith('_latency')]
        for field in latency_fields:
            assert isinstance(result[field], int), f"Invalid latency type for {field}: {type(result[field])}"
            assert result[field] >= 0, f"Negative latency for {field}: {result[field]}"
    
    def test_output_format_ndjson(self):
        """Test that output format matches NDJSON requirements"""
        calculator = MetricsCalculator()
        
        model_info = ModelInfo(
            name="test/format-model",
            url="https://huggingface.co/test/format-model",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=['text-generation'],
            likes=100,
            downloads=1000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        # Mock all calculations to get consistent output
        with patch.object(calculator.license_metric, 'calculate', return_value=0.9), \
             patch.object(calculator.size_metric, 'calculate', return_value={'raspberry_pi': 0.5, 'jetson_nano': 0.8, 'desktop_pc': 1.0, 'aws_server': 1.0}), \
             patch.object(calculator.rampup_metric, 'calculate', return_value=0.7), \
             patch.object(calculator.busfactor_metric, 'calculate', return_value=0.6), \
             patch.object(calculator.performance_metric, 'calculate', return_value=0.5), \
             patch.object(calculator.dataset_code_metric, 'calculate', return_value=0.4), \
             patch.object(calculator.dataset_quality_metric, 'calculate', return_value=0.3), \
             patch.object(calculator.code_quality_metric, 'calculate', return_value=0.8):
            
            result = calculator.calculate_all_metrics(model_info)
            
            # Test that result can be serialized to JSON
            json_str = json.dumps(result)
            assert isinstance(json_str, str)
            
            # Test that JSON can be parsed back
            parsed_result = json.loads(json_str)
            assert parsed_result == result
            
            # Verify NDJSON format (one JSON object per line)
            lines = json_str.split('\n')
            assert len(lines) == 1  # Should be one line for NDJSON
            
            # Verify all required fields are present and have correct types
            assert isinstance(parsed_result['name'], str)
            assert isinstance(parsed_result['category'], str)
            assert isinstance(parsed_result['net_score'], (int, float))
            assert isinstance(parsed_result['net_score_latency'], int)
            assert isinstance(parsed_result['size_score'], dict)
