#!/usr/bin/env python3
"""
Metrics Validator Module: Validate JSON data against metric patterns.
Supports wildcards and multiple input formats.
"""

import json
import yaml
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class MetricsValidator:
    """Main validator class for metric pattern matching."""
    
    def __init__(self):
        """Initialize metrics validator."""
        self.validation_results = {
            'found_metrics': [],
            'missing_metrics': [],
            'total_expected': 0,
            'total_found': 0,
            'validation_config': None
        }
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load validation configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Dict: Configuration data
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise
    
    def detect_format(self, data: Any) -> str:
        """
        Detect if data is in NameValuePair or ObjectHierarchy format.
        
        Args:
            data: Input data
            
        Returns:
            str: 'namevalue' or 'objecthierarchy'
        """
        if isinstance(data, dict):
            # Check if it's NameValuePair (flat with dot notation)
            sample_keys = list(data.keys())[:5]  # Check first 5 keys
            has_dot_notation = any('.' in str(key) for key in sample_keys)
            
            if has_dot_notation:
                return 'namevalue'
            else:
                return 'objecthierarchy'
        else:
            return 'unknown'
    
    def flatten_object_hierarchy(self, data: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """
        Flatten ObjectHierarchy to NameValuePair format for pattern matching.
        
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
    
    def pattern_to_regex(self, pattern: str) -> str:
        """
        Convert pattern with wildcards to regex.
        
        Args:
            pattern: Pattern with wildcards (% or * or {i})
            
        Returns:
            str: Regex pattern
        """
        # Replace different wildcard types with regex
        regex_pattern = pattern
        regex_pattern = re.sub(r'%', r'[^.]*', regex_pattern)  # % matches any non-dot characters
        regex_pattern = re.sub(r'\*', r'[^.]*', regex_pattern)  # * matches any non-dot characters
        regex_pattern = re.sub(r'\{i\}', r'[0-9]+', regex_pattern)  # {i} matches numbers
        
        # Escape dots and other special characters
        regex_pattern = re.sub(r'\.', r'\.', regex_pattern)
        
        return f"^{regex_pattern}$"
    
    def find_matching_keys(self, data: Dict[str, Any], pattern: str) -> List[str]:
        """
        Find keys that match a pattern with wildcards.
        
        Args:
            data: Flattened data dictionary
            pattern: Pattern to match
            
        Returns:
            List[str]: List of matching keys
        """
        regex_pattern = self.pattern_to_regex(pattern)
        matching_keys = []
        
        for key in data.keys():
            if re.match(regex_pattern, key):
                matching_keys.append(key)
        
        return matching_keys
    
    def validate_metrics(self, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against metric patterns in configuration.
        
        Args:
            data: Input data (NameValuePair or ObjectHierarchy)
            config: Validation configuration
            
        Returns:
            Dict: Validation results
        """
        # Detect format and flatten if necessary
        format_type = self.detect_format(data)
        logger.info(f"Detected format: {format_type}")
        
        if format_type == 'objecthierarchy':
            flattened_data = self.flatten_object_hierarchy(data)
        elif format_type == 'namevalue':
            flattened_data = data
        else:
            raise ValueError(f"Unsupported data format: {format_type}")
        
        # Initialize results
        self.validation_results = {
            'found_metrics': [],
            'missing_metrics': [],
            'total_expected': 0,
            'total_found': 0,
            'total_instances': 0,
            'validation_config': config.get('name', 'Unknown')
        }
        
        # Process each rule
        for rule in config.get('rules', []):
            rule_name = rule.get('name', 'Unknown Rule')
            patterns = rule.get('patterns', [])
            
            logger.info(f"Processing rule: {rule_name}")
            
            for pattern in patterns:
                self.validation_results['total_expected'] += 1
                
                # Find matching keys
                matching_keys = self.find_matching_keys(flattened_data, pattern)
                
                if matching_keys:
                    # Found matches (binary logic: pattern found)
                    self.validation_results['total_found'] += 1
                    self.validation_results['total_instances'] += len(matching_keys)
                    
                    # Store pattern with instance count
                    self.validation_results['found_metrics'].append({
                        'pattern': pattern,
                        'instances_found': len(matching_keys),
                        'instance_keys': matching_keys,
                        'rule': rule_name
                    })
                else:
                    # No matches found
                    self.validation_results['missing_metrics'].append({
                        'pattern': pattern,
                        'rule': rule_name
                    })
        
        return self.validation_results
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        return {
            'total_expected': self.validation_results['total_expected'],
            'total_found': self.validation_results['total_found'],
            'total_missing': len(self.validation_results['missing_metrics']),
            'total_instances': self.validation_results['total_instances'],
            'success_rate': (self.validation_results['total_found'] / self.validation_results['total_expected'] * 100) if self.validation_results['total_expected'] > 0 else 0,
            'config_name': self.validation_results['validation_config']
        }
    
    def get_found_metrics_summary(self) -> str:
        """Get a formatted summary of found metrics."""
        if not self.validation_results['found_metrics']:
            return "No metrics found."
        
        summary = []
        for metric in self.validation_results['found_metrics']:
            summary.append(f"✅ {metric['pattern']} ({metric['instances_found']} instances)")
        
        return "\n".join(summary)
    
    def get_missing_metrics_summary(self) -> str:
        """Get a formatted summary of missing metrics."""
        if not self.validation_results['missing_metrics']:
            return "No missing metrics."
        
        summary = []
        for metric in self.validation_results['missing_metrics']:
            summary.append(f"❌ {metric['pattern']}")
        
        return "\n".join(summary)

class ValidationManager:
    """Manager class for handling validation operations with Streamlit integration."""
    
    def __init__(self):
        """Initialize validation manager."""
        self.validator = MetricsValidator()
        self.config_dir = Path("config")
    
    def get_available_configs(self) -> List[Dict[str, str]]:
        """Get list of available configuration files."""
        configs = []
        
        for config_file in self.config_dir.glob("*_rules.yaml"):
            try:
                config = self.validator.load_config(str(config_file))
                configs.append({
                    'name': config.get('name', config_file.stem),
                    'description': config.get('description', ''),
                    'version': config.get('version', '1.0'),
                    'file_path': str(config_file)
                })
            except Exception as e:
                logger.error(f"Error loading config {config_file}: {e}")
        
        return configs
    
    def validate_data(self, data: Any, config_path: str) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validate data against configuration.
        
        Args:
            data: Input data
            config_path: Path to configuration file
            
        Returns:
            Tuple: (success, results, error_message)
        """
        try:
            config = self.validator.load_config(config_path)
            results = self.validator.validate_metrics(data, config)
            return True, results, ""
        except Exception as e:
            return False, {}, str(e)
    
    def validate_with_custom_config(self, data: Any, custom_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Validate data against custom configuration.
        
        Args:
            data: Input data
            custom_config: Custom configuration dictionary
            
        Returns:
            Tuple: (success, results, error_message)
        """
        try:
            results = self.validator.validate_metrics(data, custom_config)
            return True, results, ""
        except Exception as e:
            return False, {}, str(e) 