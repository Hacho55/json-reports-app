#!/usr/bin/env python3
"""
Unit tests for metrics extraction functionality.
"""

import pytest
import json
from tools.metrics_extractor import MetricsExtractor, ExtractionManager


class TestMetricsExtractor:
    """Test cases for MetricsExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MetricsExtractor()
        
        # Test data
        self.namevalue_data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
            "Device.WiFi.Radio.2.Stats.BytesSent": 2000,
            "Device.WiFi.Radio.1.Stats.BytesReceived": 500,
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.DeviceInfo.ModelName": "TestModel"
        }
        
        self.hierarchy_data = {
            "Device": {
                "WiFi": {
                    "Radio": {
                        "1": {
                            "Stats": {
                                "BytesSent": 1000,
                                "BytesReceived": 500
                            }
                        },
                        "2": {
                            "Stats": {
                                "BytesSent": 2000
                            }
                        }
                    }
                },
                "DeviceInfo": {
                    "SerialNumber": "FVN22",
                    "ModelName": "TestModel"
                }
            }
        }
    
    def test_extract_metrics_from_namevalue(self):
        """Test extraction from NameValuePair format."""
        metrics = self.extractor.extract_metrics_from_namevalue(self.namevalue_data)
        
        expected_metrics = [
            "Device.DeviceInfo.ModelName",
            "Device.DeviceInfo.SerialNumber",
            "Device.WiFi.Radio.*.Stats.BytesReceived",
            "Device.WiFi.Radio.*.Stats.BytesSent"
        ]
        
        assert len(metrics) == 4
        assert sorted(metrics) == sorted(expected_metrics)
    
    def test_extract_metrics_from_objecthierarchy(self):
        """Test extraction from ObjectHierarchy format."""
        metrics = self.extractor.extract_metrics_from_objecthierarchy(self.hierarchy_data)
        
        expected_metrics = [
            "Device.DeviceInfo.ModelName",
            "Device.DeviceInfo.SerialNumber",
            "Device.WiFi.Radio.*.Stats.BytesReceived",
            "Device.WiFi.Radio.*.Stats.BytesSent"
        ]
        
        assert len(metrics) == 4
        assert sorted(metrics) == sorted(expected_metrics)
    
    def test_convert_to_wildcard_pattern(self):
        """Test conversion of specific keys to wildcard patterns."""
        test_cases = [
            ("Device.WiFi.Radio.1.Stats.BytesSent", "Device.WiFi.Radio.*.Stats.BytesSent"),
            ("Device.DeviceInfo.SerialNumber", "Device.DeviceInfo.SerialNumber"),
            ("Device.WiFi.Radio.2.Stats.BytesReceived", "Device.WiFi.Radio.*.Stats.BytesReceived"),
            ("Device.WiFi.SSID.1.SSID", "Device.WiFi.SSID.*.SSID")
        ]
        
        for input_key, expected_pattern in test_cases:
            result = self.extractor._convert_to_wildcard_pattern(input_key)
            assert result == expected_pattern
    
    def test_flatten_hierarchy(self):
        """Test flattening of hierarchical data."""
        flattened = self.extractor._flatten_hierarchy(self.hierarchy_data)
        
        expected_keys = [
            "Device.WiFi.Radio.1.Stats.BytesSent",
            "Device.WiFi.Radio.1.Stats.BytesReceived",
            "Device.WiFi.Radio.2.Stats.BytesSent",
            "Device.DeviceInfo.SerialNumber",
            "Device.DeviceInfo.ModelName"
        ]
        
        assert len(flattened) == 5
        for key in expected_keys:
            assert key in flattened
    
    def test_categorize_metrics(self):
        """Test categorization of metrics."""
        metrics = [
            "Device.WiFi.Radio.*.Stats.BytesSent",
            "Device.DeviceInfo.SerialNumber",
            "Device.WiFi.SSID.*.SSID"
        ]
        
        categories = self.extractor.categorize_metrics(metrics)
        
        # Should be categorized by two levels now
        assert "WiFi Configuration" in categories
        assert "Device Information" in categories
        assert len(categories["WiFi Configuration"]) == 2  # WiFi metrics
        assert len(categories["Device Information"]) == 1  # DeviceInfo metrics
    
    def test_get_category_name(self):
        """Test category name mapping."""
        test_cases = [
            # Single level categories
            ("Device", "Device Information"),
            ("WiFi", "WiFi Configuration"),
            ("Ethernet", "Ethernet Interface"),
            ("Unknown", "Unknown Metrics"),
            
            # Two level categories
            ("Device.WiFi", "WiFi Configuration"),
            ("Device.DeviceInfo", "Device Information"),
            ("Device.Hosts", "Host Information"),
            ("InternetGatewayDevice.WANDevice", "WAN Device")
        ]
        
        for category_key, expected_name in test_cases:
            result = self.extractor._get_category_name(category_key)
            assert result == expected_name
    
    def test_generate_simple_list(self):
        """Test generation of simple list."""
        metrics = [
            "Device.WiFi.Radio.*.Stats.BytesSent",
            "Device.DeviceInfo.SerialNumber"
        ]
        
        result = self.extractor.generate_simple_list(metrics)
        expected = "Device.DeviceInfo.SerialNumber\nDevice.WiFi.Radio.*.Stats.BytesSent"
        
        assert result == expected
    
    def test_generate_yaml_rules(self):
        """Test generation of YAML rules."""
        metrics = [
            "Device.WiFi.Radio.*.Stats.BytesSent",
            "Device.DeviceInfo.SerialNumber"
        ]
        
        yaml_content = self.extractor.generate_yaml_rules(metrics, "Test Rules")
        
        assert "name: \"Test Rules\"" in yaml_content
        assert "Device.WiFi.Radio.*.Stats.BytesSent" in yaml_content
        assert "Device.DeviceInfo.SerialNumber" in yaml_content
    
    def test_generate_markdown_doc(self):
        """Test generation of Markdown documentation."""
        metrics = [
            "Device.WiFi.Radio.*.Stats.BytesSent",
            "Device.DeviceInfo.SerialNumber"
        ]
        
        markdown_content = self.extractor.generate_markdown_doc(metrics, "Test Doc")
        
        assert "# Test Doc" in markdown_content
        assert "Device.WiFi.Radio.*.Stats.BytesSent" in markdown_content
        assert "Device.DeviceInfo.SerialNumber" in markdown_content
        assert "| Metric | TR-181 DataType | Output Type | DB Output Name | Notes |" in markdown_content


class TestExtractionManager:
    """Test cases for ExtractionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ExtractionManager()
        
        self.test_data = {
            "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
            "Device.DeviceInfo.SerialNumber": "FVN22"
        }
    
    def test_extract_metrics_success(self):
        """Test successful metric extraction."""
        success, metrics, error = self.manager.extract_metrics(self.test_data)
        
        assert success is True
        assert len(metrics) == 2
        assert error == ""
    
    def test_extract_metrics_invalid_data(self):
        """Test extraction with invalid data."""
        success, metrics, error = self.manager.extract_metrics("invalid")
        
        assert success is False
        assert len(metrics) == 0
        assert "Invalid data format" in error
    
    def test_generate_yaml_rules(self):
        """Test YAML rules generation."""
        metrics = ["Device.WiFi.Radio.*.Stats.BytesSent"]
        yaml_content = self.manager.generate_yaml_rules(metrics, "Test")
        
        assert "name: \"Test\"" in yaml_content
        assert "Device.WiFi.Radio.*.Stats.BytesSent" in yaml_content
    
    def test_generate_markdown_doc(self):
        """Test Markdown documentation generation."""
        metrics = ["Device.WiFi.Radio.*.Stats.BytesSent"]
        markdown_content = self.manager.generate_markdown_doc(metrics, "Test")
        
        assert "# Test" in markdown_content
        assert "Device.WiFi.Radio.*.Stats.BytesSent" in markdown_content
    
    def test_generate_simple_list(self):
        """Test simple list generation."""
        metrics = ["Device.WiFi.Radio.*.Stats.BytesSent"]
        simple_list = self.manager.generate_simple_list(metrics)
        
        assert simple_list == "Device.WiFi.Radio.*.Stats.BytesSent"
    
    def test_categorize_metrics(self):
        """Test metric categorization."""
        metrics = ["Device.WiFi.Radio.*.Stats.BytesSent", "Device.DeviceInfo.SerialNumber"]
        categories = self.manager.categorize_metrics(metrics)
        
        # Should be categorized by two levels now
        assert "WiFi Configuration" in categories
        assert "Device Information" in categories
        assert len(categories["WiFi Configuration"]) == 1  # WiFi metric
        assert len(categories["Device Information"]) == 1  # DeviceInfo metric 