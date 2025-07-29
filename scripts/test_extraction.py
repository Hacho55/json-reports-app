#!/usr/bin/env python3
"""
Test script for metrics extraction functionality.
"""

import json
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.metrics_extractor import ExtractionManager

def test_extraction():
    """Test the extraction functionality."""
    
    # Sample data with specific instances
    test_data_namevalue = {
        "Device.WiFi.Radio.1.Stats.BytesSent": 1000,
        "Device.WiFi.Radio.2.Stats.BytesSent": 2000,
        "Device.WiFi.Radio.1.Stats.BytesReceived": 500,
        "Device.WiFi.Radio.2.Stats.BytesReceived": 1500,
        "Device.DeviceInfo.SerialNumber": "FVN22",
        "Device.DeviceInfo.ModelName": "TestModel",
        "Device.WiFi.SSID.1.SSID": "MyWiFi",
        "Device.WiFi.SSID.2.SSID": "GuestWiFi"
    }
    
    test_data_hierarchy = {
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
                            "BytesSent": 2000,
                            "BytesReceived": 1500
                        }
                    }
                },
                "SSID": {
                    "1": {
                        "SSID": "MyWiFi"
                    },
                    "2": {
                        "SSID": "GuestWiFi"
                    }
                }
            },
            "DeviceInfo": {
                "SerialNumber": "FVN22",
                "ModelName": "TestModel"
            }
        }
    }
    
    print("🧪 Testing Metrics Extraction")
    print("=" * 50)
    
    # Initialize extraction manager
    extraction_manager = ExtractionManager()
    
    # Test NameValuePair extraction
    print("\n📋 Testing NameValuePair extraction...")
    success, metrics, error = extraction_manager.extract_metrics(test_data_namevalue)
    
    if success:
        print("✅ NameValuePair extraction successful!")
        print(f"📊 Extracted {len(metrics)} metrics:")
        for metric in sorted(metrics):
            print(f"   - {metric}")
        
        # Test categorization
        categories = extraction_manager.categorize_metrics(metrics)
        print(f"\n📁 Categories ({len(categories)}):")
        for category, patterns in categories.items():
            print(f"   - {category}: {len(patterns)} metrics")
        
        # Test YAML generation
        yaml_rules = extraction_manager.generate_yaml_rules(metrics, "Test Extraction")
        print(f"\n⚙️ YAML Rules generated ({len(yaml_rules)} characters)")
        
        # Test Markdown generation
        markdown_doc = extraction_manager.generate_markdown_doc(metrics, "Test Extraction")
        print(f"📚 Markdown documentation generated ({len(markdown_doc)} characters)")
        
        # Test simple list
        simple_list = extraction_manager.generate_simple_list(metrics)
        print(f"📄 Simple list generated ({len(simple_list)} characters)")
        
    else:
        print(f"❌ NameValuePair extraction failed: {error}")
    
    # Test ObjectHierarchy extraction
    print("\n📋 Testing ObjectHierarchy extraction...")
    success, metrics, error = extraction_manager.extract_metrics(test_data_hierarchy)
    
    if success:
        print("✅ ObjectHierarchy extraction successful!")
        print(f"📊 Extracted {len(metrics)} metrics:")
        for metric in sorted(metrics):
            print(f"   - {metric}")
        
        # Test categorization
        categories = extraction_manager.categorize_metrics(metrics)
        print(f"\n📁 Categories ({len(categories)}):")
        for category, patterns in categories.items():
            print(f"   - {category}: {len(patterns)} metrics")
        
    else:
        print(f"❌ ObjectHierarchy extraction failed: {error}")
    
    print("\n🎉 Extraction test completed!")

if __name__ == "__main__":
    test_extraction() 