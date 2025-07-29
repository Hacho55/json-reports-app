#!/usr/bin/env python3
"""
Metrics Extractor Module: Extract metrics from JSON and convert to wildcard patterns.
"""

import json
import re
import logging
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class MetricsExtractor:
    """Extract metrics from JSON and convert to wildcard patterns."""
    
    def __init__(self):
        """Initialize metrics extractor."""
        self.extracted_metrics = []
        self.categories = {}
    
    def extract_metrics_from_namevalue(self, data: Dict[str, Any]) -> List[str]:
        """
        Extract metrics from NameValuePair format.
        
        Args:
            data: Flat dictionary with dot notation keys
            
        Returns:
            List[str]: List of extracted metric patterns
        """
        patterns = set()
        
        for key in data.keys():
            # Convert specific instances to wildcard patterns
            pattern = self._convert_to_wildcard_pattern(key)
            patterns.add(pattern)
        
        return sorted(list(patterns))
    
    def extract_metrics_from_objecthierarchy(self, data: Dict[str, Any]) -> List[str]:
        """
        Extract metrics from ObjectHierarchy format.
        
        Args:
            data: Hierarchical dictionary
            
        Returns:
            List[str]: List of extracted metric patterns
        """
        # First flatten the hierarchy
        flattened = self._flatten_hierarchy(data)
        # Then extract patterns
        return self.extract_metrics_from_namevalue(flattened)
    
    def _flatten_hierarchy(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten ObjectHierarchy to NameValuePair format.
        
        Args:
            data: Hierarchical data
            prefix: Current path prefix
            
        Returns:
            Dict: Flattened data with dot notation
        """
        flattened = {}
        
        def flatten_recursive(obj, current_prefix):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{current_prefix}.{key}" if current_prefix else key
                    if isinstance(value, (dict, list)):
                        flatten_recursive(value, new_prefix)
                    else:
                        flattened[new_prefix] = value
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_prefix = f"{current_prefix}[{i}]"
                    if isinstance(item, (dict, list)):
                        flatten_recursive(item, new_prefix)
                    else:
                        flattened[new_prefix] = item
        
        flatten_recursive(data, prefix)
        return flattened
    
    def _convert_to_wildcard_pattern(self, key: str) -> str:
        """
        Convert a specific metric key to a wildcard pattern.
        
        Args:
            key: Specific metric key (e.g., "Device.WiFi.Radio.1.Stats.BytesSent")
            
        Returns:
            str: Wildcard pattern (e.g., "Device.WiFi.Radio.*.Stats.BytesSent")
        """
        # Split by dots
        parts = key.split('.')
        pattern_parts = []
        
        for part in parts:
            # Check if part is a number (likely an index)
            if part.isdigit():
                pattern_parts.append('*')
            else:
                pattern_parts.append(part)
        
        return '.'.join(pattern_parts)
    
    def categorize_metrics(self, metrics: List[str]) -> Dict[str, List[str]]:
        """
        Categorize metrics by their first and second level.
        
        Args:
            metrics: List of metric patterns
            
        Returns:
            Dict: Categories with their metrics
        """
        categories = defaultdict(list)
        
        for metric in metrics:
            parts = metric.split('.')
            
            if len(parts) >= 2:
                # Use first and second level (e.g., "Device.WiFi" from "Device.WiFi.Radio.*.Stats.BytesSent")
                first_level = parts[0]
                second_level = parts[1]
                category_key = f"{first_level}.{second_level}"
                category_name = self._get_category_name(category_key)
            elif len(parts) == 1:
                # Single level metric
                category_name = self._get_category_name(parts[0])
            else:
                # Empty or invalid metric
                category_name = "Other"
            
            categories[category_name].append(metric)
        
        return dict(categories)
    
    def _get_category_name(self, category_key: str) -> str:
        """
        Get a human-readable category name.
        
        Args:
            category_key: Category key (e.g., "Device.WiFi" or "Device")
            
        Returns:
            str: Category name
        """
        category_mapping = {
            # Single level categories
            'Device': 'Device Information',
            'InternetGatewayDevice': 'Gateway Device',
            'Hosts': 'Host Information',
            'WiFi': 'WiFi Configuration',
            'Ethernet': 'Ethernet Interface',
            'IP': 'IP Interface',
            'WAN': 'WAN Interface',
            'LAN': 'LAN Interface',
            
            # Two level categories
            'Device.DeviceInfo': 'Device Information',
            'Device.WiFi': 'WiFi Configuration',
            'Device.Hosts': 'Host Information',
            'Device.Ethernet': 'Ethernet Interface',
            'Device.IP': 'IP Interface',
            'Device.WAN': 'WAN Interface',
            'Device.LAN': 'LAN Interface',
            'Device.ManagementServer': 'Management Server',
            'Device.Firewall': 'Firewall Configuration',
            'Device.ProcessStatus': 'Process Status',
            'Device.MemoryStatus': 'Memory Status',
            'InternetGatewayDevice.WANDevice': 'WAN Device',
            'InternetGatewayDevice.LANDevice': 'LAN Device',
            'InternetGatewayDevice.WANConnectionDevice': 'WAN Connection',
            'InternetGatewayDevice.LANHostConfigManagement': 'LAN Host Config',
            'InternetGatewayDevice.Layer2Bridging': 'Layer 2 Bridging',
            'InternetGatewayDevice.QoS': 'Quality of Service',
            'InternetGatewayDevice.UploadDiagnostics': 'Upload Diagnostics',
            'InternetGatewayDevice.DownloadDiagnostics': 'Download Diagnostics'
        }
        
        return category_mapping.get(category_key, f"{category_key} Metrics")
    
    def generate_yaml_rules(self, metrics: List[str], name: str = "Extracted Metrics") -> str:
        """
        Generate YAML rules from extracted metrics.
        
        Args:
            metrics: List of metric patterns
            name: Name for the configuration
            
        Returns:
            str: YAML content
        """
        categories = self.categorize_metrics(metrics)
        
        yaml_content = f"""# {name}
# Extracted metrics from JSON data

name: "{name}"
description: "Metrics extracted from JSON data"
version: "1.0"

rules:
"""
        
        for category, patterns in categories.items():
            yaml_content += f"""  - name: "{category}"
    description: "{category} metrics"
    category: "{category}"
    patterns:
"""
            for pattern in sorted(patterns):
                yaml_content += f"      - \"{pattern}\"\n"
        
        return yaml_content
    
    def generate_markdown_doc(self, metrics: List[str], title: str = "Extracted Metrics") -> str:
        """
        Generate Markdown documentation similar to wei_tr181_metrics.md.
        
        Args:
            metrics: List of metric patterns
            title: Title for the document
            
        Returns:
            str: Markdown content
        """
        categories = self.categorize_metrics(metrics)
        
        markdown_content = f"""# {title}

**Generated from:** JSON data extraction
**Notes:** This document lists all metrics extracted from the provided JSON data.

---

"""
        
        for category, patterns in categories.items():
            markdown_content += f"""### {category}

| Metric | TR-181 DataType | Output Type | DB Output Name | Notes |
|---|---|---|---|---|
"""
            
            for pattern in sorted(patterns):
                markdown_content += f"| `{pattern}` |  |  |  |  |\n"
            
            markdown_content += "\n"
        
        return markdown_content
    
    def generate_simple_list(self, metrics: List[str]) -> str:
        """
        Generate a simple list of metrics.
        
        Args:
            metrics: List of metric patterns
            
        Returns:
            str: Simple list content
        """
        return "\n".join(sorted(metrics))

class ExtractionManager:
    """Manager class for handling metric extraction operations."""
    
    def __init__(self):
        """Initialize extraction manager."""
        self.extractor = MetricsExtractor()
    
    def extract_metrics(self, data: Any) -> Tuple[bool, List[str], str]:
        """
        Extract metrics from JSON data.
        
        Args:
            data: JSON data (NameValuePair or ObjectHierarchy)
            
        Returns:
            Tuple: (success, metrics, error_message)
        """
        try:
            # Detect format
            if isinstance(data, dict):
                # Check if it's NameValuePair (flat with dot notation)
                sample_keys = list(data.keys())[:5]  # Check first 5 keys
                has_dot_notation = any('.' in str(key) for key in sample_keys)
                
                if has_dot_notation:
                    # NameValuePair format
                    metrics = self.extractor.extract_metrics_from_namevalue(data)
                else:
                    # ObjectHierarchy format
                    metrics = self.extractor.extract_metrics_from_objecthierarchy(data)
            else:
                return False, [], "Invalid data format"
            
            return True, metrics, ""
            
        except Exception as e:
            logger.error(f"Error extracting metrics: {e}")
            return False, [], str(e)
    
    def generate_yaml_rules(self, metrics: List[str], name: str = "Extracted Metrics") -> str:
        """Generate YAML rules from metrics."""
        return self.extractor.generate_yaml_rules(metrics, name)
    
    def generate_markdown_doc(self, metrics: List[str], title: str = "Extracted Metrics") -> str:
        """Generate Markdown documentation from metrics."""
        return self.extractor.generate_markdown_doc(metrics, title)
    
    def generate_simple_list(self, metrics: List[str]) -> str:
        """Generate simple list from metrics."""
        return self.extractor.generate_simple_list(metrics)
    
    def categorize_metrics(self, metrics: List[str]) -> Dict[str, List[str]]:
        """Categorize metrics by first level."""
        return self.extractor.categorize_metrics(metrics) 