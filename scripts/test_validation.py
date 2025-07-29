#!/usr/bin/env python3
"""
Test script for metrics validation with instance counting.
"""

import json
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.metrics_validator import ValidationManager

def test_validation_with_instances():
    """Test validation with instance counting."""
    
    # Sample data with multiple instances
    test_data = {
        "Device.WiFi.DataElements.1.Radio.1.BSS.1.STA.1.LastConnectTime": "2024-01-01T10:00:00Z",
        "Device.WiFi.DataElements.1.Radio.1.BSS.1.STA.2.LastConnectTime": "2024-01-01T11:00:00Z",
        "Device.WiFi.DataElements.1.Radio.2.BSS.1.STA.1.LastConnectTime": "2024-01-01T12:00:00Z",
        "Device.WiFi.DataElements.2.Radio.1.BSS.1.STA.1.LastConnectTime": "2024-01-01T13:00:00Z",
        "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
        "Device.WiFi.Radio.2.Stats.BytesSent": 2000,
        "Device.DeviceInfo.SerialNumber": "TEST123",
        "Device.DeviceInfo.ModelName": "TestModel"
    }
    
    # Custom config for testing
    test_config = {
        "name": "Test Validation",
        "description": "Test configuration for instance counting",
        "version": "1.0",
        "rules": [
            {
                "name": "WiFi Data Elements Test",
                "description": "Test WiFi data elements",
                "category": "WiFi",
                "patterns": [
                    "Device.WiFi.DataElements.%.Radio.%.BSS.%.STA.%.LastConnectTime"
                ]
            },
            {
                "name": "WiFi Radio Statistics Test",
                "description": "Test WiFi radio statistics",
                "category": "WiFi",
                "patterns": [
                    "Device.WiFi.Radio.%.Stats.BytesSent"
                ]
            },
            {
                "name": "Device Information Test",
                "description": "Test device information",
                "category": "Device",
                "patterns": [
                    "Device.DeviceInfo.SerialNumber",
                    "Device.DeviceInfo.ModelName"
                ]
            },
            {
                "name": "Missing Pattern Test",
                "description": "Test missing pattern",
                "category": "Test",
                "patterns": [
                    "Device.WiFi.Radio.%.Stats.NonExistentMetric"
                ]
            }
        ]
    }
    
    # Initialize validation manager
    validation_manager = ValidationManager()
    
    # Run validation
    success, results, error = validation_manager.validate_with_custom_config(test_data, test_config)
    
    if success:
        print("✅ Validation completed successfully!")
        print(f"📊 Results:")
        print(f"   - Total Expected: {results['total_expected']}")
        print(f"   - Total Found: {results['total_found']}")
        print(f"   - Total Instances: {results['total_instances']}")
        print(f"   - Total Missing: {len(results['missing_metrics'])}")
        
        print(f"\n✅ Found Metrics:")
        for metric in results['found_metrics']:
            print(f"   - {metric['pattern']}: {metric['instances_found']} instances")
        
        print(f"\n❌ Missing Metrics:")
        for metric in results['missing_metrics']:
            print(f"   - {metric['pattern']}")
        
        # Test statistics
        stats = validation_manager.validator.get_validation_stats()
        print(f"\n📈 Statistics:")
        print(f"   - Success Rate: {stats['success_rate']:.1f}%")
        print(f"   - Config: {stats['config_name']}")
        
    else:
        print(f"❌ Validation failed: {error}")

if __name__ == "__main__":
    test_validation_with_instances() 