#!/usr/bin/env python3
"""
Unit tests for JSON converter functionality.
"""

import pytest
import json
from tools.json_converter import ConversionManager, JSONConverter


class TestJSONConverter:
    """Test cases for JSONConverter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = JSONConverter()
    
    def test_to_name_value_pair_simple(self):
        """Test simple ObjectHierarchy to NameValuePair conversion."""
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
        
        result = self.converter.to_name_value_pair(input_data)
        
        expected = {
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.WiFi.Radio.1.Channel": "6"
        }
        
        assert result == expected
    
    def test_to_object_hierarchy_simple(self):
        """Test simple NameValuePair to ObjectHierarchy conversion."""
        input_data = {
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.WiFi.Radio.1.Channel": "6"
        }
        
        result = self.converter.to_object_hierarchy(input_data)
        
        expected = {
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
        
        assert result == expected
    
    def test_deep_bytes_to_str(self):
        """Test bytes to string conversion."""
        input_data = {
            "key1": b"value1",
            "key2": "value2",
            "nested": {
                "key3": b"value3"
            }
        }
        
        # Import the function directly
        from tools.json_converter import deep_bytes_to_str
        result = deep_bytes_to_str(input_data)
        
        expected = {
            "key1": "value1",
            "key2": "value2",
            "nested": {
                "key3": "value3"
            }
        }
        
        assert result == expected


class TestConversionManager:
    """Test cases for ConversionManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = ConversionManager()
    
    def test_convert_data_to_namevalue(self):
        """Test conversion to NameValuePair via manager."""
        input_data = {
            "Device": {
                "DeviceInfo": {
                    "SerialNumber": "FVN22"
                }
            }
        }
        
        success, result, error = self.manager.convert_data(input_data, 'to_namevalue')
        
        assert success is True
        assert error == ""  # Error is empty string, not None
        assert "Device.DeviceInfo.SerialNumber" in result
    
    def test_convert_data_to_hierarchy(self):
        """Test conversion to ObjectHierarchy via manager."""
        input_data = {
            "Device.DeviceInfo.SerialNumber": "FVN22"
        }
        
        success, result, error = self.manager.convert_data(input_data, 'to_hierarchy')
        
        assert success is True
        assert error == ""  # Error is empty string, not None
        assert "Device" in result
    
    def test_convert_data_invalid_direction(self):
        """Test conversion with invalid direction."""
        input_data = {"test": "data"}
        
        success, result, error = self.manager.convert_data(input_data, 'invalid')
        
        assert success is False
        assert error is not None
    
    def test_get_conversion_stats(self):
        """Test conversion statistics."""
        stats = self.manager.get_conversion_stats()
        
        assert isinstance(stats, dict)
        assert 'total_keys' in stats
        assert 'processed_keys' in stats
        assert 'errors' in stats
        assert 'conversion_type' in stats
    
    def test_get_sample_output(self):
        """Test sample output generation."""
        data = {
            "Device.DeviceInfo.SerialNumber": "FVN22",
            "Device.WiFi.Radio.1.Channel": "6"
        }
        
        sample = self.manager.get_sample_output(data)
        
        assert isinstance(sample, str)
        assert "Device.DeviceInfo.SerialNumber" in sample 