#!/usr/bin/env python3
"""
Test script to diagnose JSON conversion issues.
"""

import json
import logging
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.json_converter import ConversionManager

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_conversion():
    """Test the conversion with sample data."""
    
    # Sample hierarchical data
    hierarchical_data = {
        "CollectionTime": "2024-01-01T00:00:00Z",
        "Device": {
            "DeviceInfo": {
                "SerialNumber": "FVN22270047E"
            },
            "WiFi": {
                "Radio": {
                    "1": {
                        "Channel": "6",
                        "SSID": "MyWiFi"
                    }
                }
            }
        }
    }
    
    # Sample NameValuePair data
    namevalue_data = {
        "CollectionTime": "2024-01-01T00:00:00Z",
        "Device.DeviceInfo.SerialNumber": "FVN22270047E",
        "Device.WiFi.Radio.1.Channel": "6",
        "Device.WiFi.Radio.1.SSID": "MyWiFi"
    }
    
    logger.info("Testing conversions with sample data")
    
    try:
        converter = ConversionManager()
        
        # Test ObjectHierarchy -> NameValuePair
        logger.info("Testing ObjectHierarchy -> NameValuePair...")
        success, result, error = converter.convert_data(hierarchical_data, 'to_namevalue')
        
        if success:
            logger.info("✅ ObjectHierarchy -> NameValuePair successful!")
            logger.info(f"Result: {json.dumps(result, indent=2)}")
        else:
            logger.error(f"❌ ObjectHierarchy -> NameValuePair failed: {error}")
        
        # Test NameValuePair -> ObjectHierarchy
        logger.info("Testing NameValuePair -> ObjectHierarchy...")
        success, result, error = converter.convert_data(namevalue_data, 'to_hierarchy')
        
        if success:
            logger.info("✅ NameValuePair -> ObjectHierarchy successful!")
            logger.info(f"Result: {json.dumps(result, indent=2)}")
        else:
            logger.error(f"❌ NameValuePair -> ObjectHierarchy failed: {error}")
            
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        logger.error(f"Exception type: {type(e)}")

if __name__ == "__main__":
    test_conversion() 