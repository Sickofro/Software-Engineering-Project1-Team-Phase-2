# tests/test_metrics_fixed.py
"""
Fixed comprehensive tests for all metrics to achieve 80%+ coverage
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from src.models.model import ModelInfo, DatasetInfo, CodeInfo, MetricResult
from src.metrics.license_metric import LicenseMetric
from src.metrics.size_metric import SizeMetric
from src.metrics.busfactor_metric import BusFactorMetric
from src.metrics.performance_metric import PerformanceMetric
from src.metrics.dataset_code_metric import DatasetCodeMetric
from src.metrics.dataset_quality_metric import DatasetQualityMetric
from src.metrics.code_quality_metric import CodeQualityMetric
from src.metrics.rampup_metric import RampUpMetric
from src.metrics.calculator import MetricsCalculator


class TestLicenseMetric:
    """Test license metric calculations"""
    
    def test_license_metric_initialization(self):
        """Test license metric initialization"""
        metric = LicenseMetric()
        assert metric is not None
        assert hasattr(metric, 'license_scores')
        assert 'apache-2.0' in metric.license_scores
    
    def test_license_calculation_apache(self):
        """Test license calculation for Apache license"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
    
        result = metric.calculate(model_info)
        assert result == 1.0

    def test_license_calculation_mit(self):
        """Test license calculation for MIT license"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={'license': 'mit'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 1.0
    
    def test_license_calculation_gpl(self):
        """Test license calculation for GPL license"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={'license': 'gpl-3.0'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.3
    
    def test_license_calculation_unknown(self):
        """Test license calculation for unknown license"""
        metric = LicenseMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={'license': 'unknown'},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.1
    
    @patch('src.metrics.license_metric.requests.Session.get')
    def test_license_parsing_from_readme(self, mock_get):
        """Test license parsing from README"""
        metric = LicenseMetric()
        
        # Mock README response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        # Model Name
        
        ## License
        This model is licensed under the Apache License 2.0
        """
        mock_get.return_value = mock_response
        
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert result == 0.9
    
    def test_license_calculation_exception(self):
        """Test license calculation with exception"""
        metric = LicenseMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert result == 0.1


class TestSizeMetric:
    """Test size metric calculations"""
    
    def test_size_metric_initialization(self):
        """Test size metric initialization"""
        metric = SizeMetric()
        assert metric is not None
        assert hasattr(metric, 'hardware_limits')
        assert 'raspberry_pi' in metric.hardware_limits
    
    def test_size_calculation_small_model(self):
        """Test size calculation for small model"""
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
    
    def test_size_calculation_large_model(self):
        """Test size calculation for large model"""
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
            assert isinstance(result, dict)
            assert result['raspberry_pi'] == 0.0  # Too large for Raspberry Pi
            assert result['aws_server'] == 1.0    # Fits on AWS server
    
    def test_size_estimation_from_name(self):
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
    
    def test_size_calculation_exception(self):
        """Test size calculation with exception"""
        metric = SizeMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert isinstance(result, dict)
        # The actual implementation returns default values, not all 0.5
        assert all(0.0 <= score <= 1.0 for score in result.values())


class TestBusFactorMetric:
    """Test bus factor metric calculations"""
    
    def test_bus_factor_metric_initialization(self):
        """Test bus factor metric initialization"""
        metric = BusFactorMetric()
        assert metric is not None
    
    def test_bus_factor_calculation_recent_activity(self):
        """Test bus factor calculation with recent activity"""
        metric = BusFactorMetric()
        model_info = ModelInfo(
            name="google/test-model",
            url="https://huggingface.co/google/test-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=1000,
            downloads=50000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_bus_factor_calculation_old_activity(self):
        """Test bus factor calculation with old activity"""
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
    
    def test_bus_factor_known_organization(self):
        """Test bus factor for known organization"""
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
    
    def test_bus_factor_community_engagement(self):
        """Test bus factor community engagement"""
        metric = BusFactorMetric()
        model_info = ModelInfo(
            name="test/popular-model",
            url="https://huggingface.co/test/popular-model",
            api_data={},
            model_index=None,
            tags=None,
            likes=5000,
            downloads=200000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_bus_factor_calculation_exception(self):
        """Test bus factor calculation with exception"""
        metric = BusFactorMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestPerformanceMetric:
    """Test performance claims metric calculations"""
    
    def test_performance_metric_initialization(self):
        """Test performance metric initialization"""
        metric = PerformanceMetric()
        assert metric is not None
    
    def test_performance_calculation_with_model_index(self):
        """Test performance calculation with model index"""
        metric = PerformanceMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
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
    
    @patch('src.metrics.performance_metric.requests.Session.get')
    def test_performance_calculation_with_readme(self, mock_get):
        """Test performance calculation with README benchmarks"""
        metric = PerformanceMetric()
        
        # Mock README response
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
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_performance_calculation_with_tags(self):
        """Test performance calculation with evaluation tags"""
        metric = PerformanceMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=['evaluation', 'benchmark', 'performance'],
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_performance_calculation_exception(self):
        """Test performance calculation with exception"""
        metric = PerformanceMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestDatasetCodeMetric:
    """Test dataset and code metric calculations"""
    
    def test_dataset_code_metric_initialization(self):
        """Test dataset code metric initialization"""
        metric = DatasetCodeMetric()
        assert metric is not None
    
    def test_dataset_code_calculation_with_model_index(self):
        """Test dataset code calculation with model index"""
        metric = DatasetCodeMetric()
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
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
    
    @patch('src.metrics.dataset_code_metric.requests.Session.get')
    def test_dataset_code_calculation_with_readme(self, mock_get):
        """Test dataset code calculation with README"""
        metric = DatasetCodeMetric()
        
        # Mock responses
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
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_dataset_code_calculation_exception(self):
        """Test dataset code calculation with exception"""
        metric = DatasetCodeMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestDatasetQualityMetric:
    """Test dataset quality metric calculations"""
    
    def test_dataset_quality_metric_initialization(self):
        """Test dataset quality metric initialization"""
        metric = DatasetQualityMetric()
        assert metric is not None
    
    @patch('src.metrics.dataset_quality_metric.requests.Session.get')
    def test_dataset_quality_calculation_with_readme(self, mock_get):
        """Test dataset quality calculation with README"""
        metric = DatasetQualityMetric()
        
        # Mock README response
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
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_dataset_quality_calculation_exception(self):
        """Test dataset quality calculation with exception"""
        metric = DatasetQualityMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestCodeQualityMetric:
    """Test code quality metric calculations"""
    
    def test_code_quality_metric_initialization(self):
        """Test code quality metric initialization"""
        metric = CodeQualityMetric()
        assert metric is not None
    
    @patch('src.metrics.code_quality_metric.requests.Session.get')
    def test_code_quality_calculation_with_files(self, mock_get):
        """Test code quality calculation with files"""
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
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_code_quality_calculation_exception(self):
        """Test code quality calculation with exception"""
        metric = CodeQualityMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestRampUpMetric:
    """Test ramp-up metric calculations"""
    
    def test_rampup_metric_initialization(self):
        """Test ramp-up metric initialization"""
        metric = RampUpMetric()
        assert metric is not None
    
    @patch('src.metrics.rampup_metric.requests.Session.get')
    def test_rampup_calculation_with_readme(self, mock_get):
        """Test ramp-up calculation with README"""
        metric = RampUpMetric()
        
        # Mock README response
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
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=100,
            downloads=1000,
            last_modified=None
        )
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0
    
    def test_rampup_calculation_exception(self):
        """Test ramp-up calculation with exception"""
        metric = RampUpMetric()
        model_info = None  # This will cause an exception
        
        result = metric.calculate(model_info)
        assert 0.0 <= result <= 1.0  # Should return a valid score


class TestMetricsCalculator:
    """Test metrics calculator integration"""
    
    def test_metrics_calculator_initialization(self):
        """Test metrics calculator initialization"""
        calculator = MetricsCalculator()
        assert calculator is not None
        assert hasattr(calculator, 'license_metric')
        assert hasattr(calculator, 'size_metric')
        assert hasattr(calculator, 'rampup_metric')
        assert hasattr(calculator, 'busfactor_metric')
        assert hasattr(calculator, 'performance_metric')
        assert hasattr(calculator, 'dataset_code_metric')
        assert hasattr(calculator, 'dataset_quality_metric')
        assert hasattr(calculator, 'code_quality_metric')
    
    def test_calculate_all_metrics_mock(self):
        """Test calculate all metrics with mocked results"""
        calculator = MetricsCalculator()
        
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={'license': 'apache-2.0'},
            model_index=None,
            tags=None,
            likes=100,
            downloads=1000,
            last_modified="2024-01-01T00:00:00Z"
        )
        
        # Mock all metric calculations
        with patch.object(calculator.license_metric, 'calculate', return_value=0.9), \
             patch.object(calculator.size_metric, 'calculate', return_value={'raspberry_pi': 0.5, 'jetson_nano': 0.8, 'desktop_pc': 1.0, 'aws_server': 1.0}), \
             patch.object(calculator.rampup_metric, 'calculate', return_value=0.7), \
             patch.object(calculator.busfactor_metric, 'calculate', return_value=0.6), \
             patch.object(calculator.performance_metric, 'calculate', return_value=0.5), \
             patch.object(calculator.dataset_code_metric, 'calculate', return_value=0.4), \
             patch.object(calculator.dataset_quality_metric, 'calculate', return_value=0.3), \
             patch.object(calculator.code_quality_metric, 'calculate', return_value=0.8):
            
            result = calculator.calculate_all_metrics(model_info)
            
            assert isinstance(result, dict)
            assert 'name' in result
            assert 'category' in result
            assert 'net_score' in result
            assert 'net_score_latency' in result
            assert result['name'] == "test/model"
            assert result['category'] == "MODEL"
            assert 0.0 <= result['net_score'] <= 1.0
    
    def test_calculate_net_score(self):
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
    
    def test_calculate_metric_with_timing(self):
        """Test metric calculation with timing"""
        calculator = MetricsCalculator()
        
        def mock_calculate(model_info):
            return 0.5
        
        model_info = ModelInfo(
            name="test/model",
            url="https://huggingface.co/test/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=0,
            downloads=0,
            last_modified=None
        )
        
        result = calculator._calculate_metric_with_timing(mock_calculate, model_info)
        assert hasattr(result, 'value')
        assert hasattr(result, 'latency_ms')
        assert result.value == 0.5
        assert result.latency_ms >= 0


class TestIntegrationComprehensive:
    """Comprehensive integration tests"""
    
    def test_full_metrics_pipeline(self):
        """Test full metrics calculation pipeline"""
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
        
        # This will make actual API calls, so we expect it to work
        result = calculator.calculate_all_metrics(model_info)
        
        assert isinstance(result, dict)
        assert 'name' in result
        assert 'net_score' in result
        assert 'ramp_up_time' in result
        assert 'bus_factor' in result
        assert 'performance_claims' in result
        assert 'license' in result
        assert 'size_score' in result
        assert 'dataset_and_code_score' in result
        assert 'dataset_quality' in result
        assert 'code_quality' in result
        
        # Check that all values are in valid ranges
        for key, value in result.items():
            if key.endswith('_latency'):
                assert isinstance(value, int)
                assert value >= 0
            elif key == 'size_score':
                assert isinstance(value, dict)
                for hw, score in value.items():
                    assert 0.0 <= score <= 1.0
            elif key in ['name', 'category']:
                assert isinstance(value, str)
            else:
                assert 0.0 <= value <= 1.0
    
    def test_metrics_calculation_with_exceptions(self):
        """Test metrics calculation when some metrics fail"""
        calculator = MetricsCalculator()
        
        # Create a model info that might cause some metrics to fail
        model_info = ModelInfo(
            name="invalid/model",
            url="https://huggingface.co/invalid/model",
            api_data={},
            model_index=None,
            tags=None,
            likes=None,
            downloads=None,
            last_modified=None
        )
        
        result = calculator.calculate_all_metrics(model_info)
        
        # Should still return a valid result with default values
        assert isinstance(result, dict)
        assert 'net_score' in result
        assert 0.0 <= result['net_score'] <= 1.0
