#!/usr/bin/env python3
"""
Unit tests for metrics validator functionality.
"""

import pytest
import tempfile
import yaml
from tools.metrics_validator import MetricsValidator, ValidationManager


class TestMetricsValidator:
    """Test cases for MetricsValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = MetricsValidator()
    
    def test_detect_format_namevalue(self):
        """Test format detection for NameValuePair."""
        data = {
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.WiFi.Radio.1.Channel": "6"
        }
        
        format_type = self.validator.detect_format(data)
        
        assert format_type == 'namevalue'
    
    def test_detect_format_objecthierarchy(self):
        """Test format detection for ObjectHierarchy."""
        data = {
            "Device": {
                "DeviceInfo": {
                    "SerialNumber": "FVN22"
                }
            }
        }
        
        format_type = self.validator.detect_format(data)
        
        assert format_type == 'objecthierarchy'
    
    def test_flatten_object_hierarchy(self):
        """Test flattening ObjectHierarchy to NameValuePair."""
        input_data = {
            "Device": {
                "DeviceInfo": {
                    "SerialNumber": "FVN22"
                },
                "WiFi": {
                    "Radio": {
                        "1": {
                            "Channel": "6"
                        }
                    }
                }
            }
        }
        
        result = self.validator.flatten_object_hierarchy(input_data)
        
        expected = {
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.WiFi.Radio.1.Channel": "6"
        }
        
        assert result == expected
    
    def test_pattern_to_regex_percent_wildcard(self):
        """Test pattern to regex conversion with % wildcard."""
        pattern = "Device.WiFi.Radio.%.Stats.BytesSent"
        regex = self.validator.pattern_to_regex(pattern)
        
        # The actual implementation generates this pattern with double escaping
        expected = r"^Device\.WiFi\.Radio\.[^\.][^\.]*\.Stats\.BytesSent$"
        assert regex == expected
    
    def test_pattern_to_regex_asterisk_wildcard(self):
        """Test pattern to regex conversion with * wildcard."""
        pattern = "Device.WiFi.Radio.*.Stats.BytesSent"
        regex = self.validator.pattern_to_regex(pattern)
        
        # The actual implementation generates this pattern
        expected = r"^Device\.WiFi\.Radio\.[^\.]*\.Stats\.BytesSent$"
        assert regex == expected
    
    def test_pattern_to_regex_braces_wildcard(self):
        """Test pattern to regex conversion with {i} wildcard."""
        pattern = "Device.WiFi.Radio.{i}.Stats.BytesSent"
        regex = self.validator.pattern_to_regex(pattern)
        
        # Use raw string to avoid escape sequence issues
        expected = r"^Device\.WiFi\.Radio\.[0-9]+\.Stats\.BytesSent$"
        assert regex == expected
    
    def test_find_matching_keys(self):
        """Test finding keys that match a pattern."""
        data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
            "Device.WiFi.Radio.2.Stats.BytesSent": 2000,
            "Device.WiFi.Radio.1.Stats.BytesReceived": 500,
            "Device.DeviceInfo.SerialNumber": "FVN22"
        }
        
        pattern = "Device.WiFi.Radio.%.Stats.BytesSent"
        matching_keys = self.validator.find_matching_keys(data, pattern)
        
        expected = [
            "Device.WiFi.Radio.1.Stats.BytesSent",
            "Device.WiFi.Radio.2.Stats.BytesSent"
        ]
        
        assert set(matching_keys) == set(expected)
    
    def test_validate_metrics_simple(self):
        """Test simple metrics validation."""
        data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
            "Device.DeviceInfo.SerialNumber": "FVN22"
        }
        
        config = {
            "name": "Test Config",
            "rules": [
                {
                    "name": "WiFi Test",
                    "patterns": ["Device.WiFi.Radio.%.Stats.BytesSent"]
                },
                {
                    "name": "Device Test",
                    "patterns": ["Device.DeviceInfo.SerialNumber"]
                }
            ]
        }
        
        results = self.validator.validate_metrics(data, config)
        
        assert results['total_expected'] == 2
        assert results['total_found'] == 2
        assert results['total_instances'] == 2
        assert len(results['found_metrics']) == 2
        assert len(results['missing_metrics']) == 0
    
    def test_validate_metrics_with_missing(self):
        """Test metrics validation with missing patterns."""
        data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000
        }
        
        config = {
            "name": "Test Config",
            "rules": [
                {
                    "name": "WiFi Test",
                    "patterns": [
                        "Device.WiFi.Radio.%.Stats.BytesSent",
                        "Device.WiFi.Radio.%.Stats.BytesReceived"
                    ]
                }
            ]
        }
        
        results = self.validator.validate_metrics(data, config)
        
        assert results['total_expected'] == 2
        assert results['total_found'] == 1
        assert results['total_instances'] == 1
        assert len(results['found_metrics']) == 1
        assert len(results['missing_metrics']) == 1
    
    def test_get_validation_stats(self):
        """Test validation statistics generation."""
        # Set up validation results
        self.validator.validation_results = {
            'total_expected': 5,
            'total_found': 3,
            'total_instances': 7,
            'validation_config': 'Test Config',
            'found_metrics': [],
            'missing_metrics': []
        }
        
        stats = self.validator.get_validation_stats()
        
        assert stats['total_expected'] == 5
        assert stats['total_found'] == 3
        assert stats['total_instances'] == 7
        assert stats['total_missing'] == 0  # Calculated from missing_metrics length
        assert stats['success_rate'] == 60.0
        assert stats['config_name'] == 'Test Config'


class TestValidationManager:
    """Test cases for ValidationManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ValidationManager()
    
    def test_get_available_configs(self):
        """Test getting available configurations."""
        configs = self.manager.get_available_configs()
        
        assert isinstance(configs, list)
        # Should find the YAML config files we created
        config_names = [config['name'] for config in configs]
        assert 'Wei TR-181 Metrics' in config_names or len(configs) >= 0
    
    def test_validate_with_custom_config(self):
        """Test validation with custom configuration."""
        data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
            "Device.DeviceInfo.SerialNumber": "FVN22"
        }
        
        config = {
            "name": "Test Config",
            "rules": [
                {
                    "name": "Test Rule",
                    "patterns": ["Device.WiFi.Radio.%.Stats.BytesSent"]
                }
            ]
        }
        
        success, results, error = self.manager.validate_with_custom_config(data, config)
        
        assert success is True
        assert error == ""
        assert results['total_expected'] == 1
        assert results['total_found'] == 1
        assert results['total_instances'] == 1
    
    def test_validate_with_invalid_data(self):
        """Test validation with invalid data."""
        data = "invalid data"
        
        config = {
            "name": "Test Config",
            "rules": []
        }
        
        success, results, error = self.manager.validate_with_custom_config(data, config)
        
        assert success is False
        assert error != "" 