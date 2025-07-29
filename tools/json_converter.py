#!/usr/bin/env python3
"""
JSON Converter Module: Convert between NameValuePair and ObjectHierarchy formats.
Modular implementation for Streamlit app with enhanced functionality.
"""

import json
import logging
from typing import Dict, Any, Union, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.WARNING, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('json_converter.log')
    ]
)
logger = logging.getLogger(__name__)

def deep_bytes_to_str(obj):
    """Recursively convert all bytes in dict/list to str."""
    if isinstance(obj, dict):
        return {deep_bytes_to_str(k): deep_bytes_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_bytes_to_str(i) for i in obj]
    elif isinstance(obj, bytes):
        logger.warning(f"Found bytes object, converting to string: {type(obj)}")
        return obj.decode('utf-8')
    else:
        return obj

class JSONConverter:
    """Main converter class for JSON format transformations."""
    
    def __init__(self):
        """Initialize JSON converter with statistics tracking."""
        self.stats = {
            'total_keys': 0,
            'processed_keys': 0,
            'errors': 0,
            'conversion_type': None
        }
    
    def to_object_hierarchy(self, data: Union[List[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert NameValuePair format to ObjectHierarchy format.
        
        Args:
            data: Input data in NameValuePair format (flat dict with dot-separated keys)
            
        Returns:
            Dict: Hierarchical structure
        """
        data = deep_bytes_to_str(data)
        
        self.stats['conversion_type'] = 'NameValuePair_to_ObjectHierarchy'
        self.stats['total_keys'] = len(data) if isinstance(data, dict) else len(data)
        self.stats['processed_keys'] = 0
        self.stats['errors'] = 0
        
        result = {}
        
        try:
            # Handle flat dictionary with dot notation (NameValuePair format)
            if isinstance(data, dict):
                for name, value in data.items():
                    self._build_hierarchy(result, str(name), value)
            
            # Handle list of NameValuePair objects (legacy format)
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    if isinstance(item, dict):
                        name = str(item.get('Name', ''))
                        value = item.get('Value', '')
                        self._build_hierarchy(result, name, value)
            
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error in to_object_hierarchy: {e}")
            raise
    
    def to_name_value_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ObjectHierarchy format to NameValuePair format.
        
        Args:
            data: Input data in ObjectHierarchy format (nested dict)
            
        Returns:
            Dict: Flat dictionary with dot-separated keys
        """
        data = deep_bytes_to_str(data)
        
        self.stats['conversion_type'] = 'ObjectHierarchy_to_NameValuePair'
        self.stats['total_keys'] = 0
        self.stats['processed_keys'] = 0
        self.stats['errors'] = 0
        
        result = {}
        
        try:
            self._flatten_hierarchy_to_dict(data, "", result)
            self.stats['total_keys'] = len(result)
            self.stats['processed_keys'] = len(result)
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error in to_name_value_pair: {e}")
            logger.error(f"Error type: {type(e)}")
            raise
    
    def _build_hierarchy(self, result: Dict[str, Any], path: str, value: Any):
        if not path:
            return
        
        try:
            # Ensure path is string
            if isinstance(path, bytes):
                path = path.decode('utf-8')
            else:
                path = str(path)
            
            # Check if path is still bytes after conversion
            if isinstance(path, bytes):
                path = path.decode('utf-8')
            
            parts = path.split('.')
            current = result
            
            # Navigate through the hierarchy, creating nodes as needed
            for i, part in enumerate(parts[:-1]):
                # Ensure part is string
                if isinstance(part, bytes):
                    part = part.decode('utf-8')
                else:
                    part = str(part)
                
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the final value
            final_part = parts[-1]
            if isinstance(final_part, bytes):
                final_part = final_part.decode('utf-8')
            else:
                final_part = str(final_part)
            
            # Ensure value is string if bytes
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            current[final_part] = value
            self.stats['processed_keys'] += 1
            
        except Exception as e:
            logger.error(f"Error in _build_hierarchy: {e}")
            raise
    
    def _flatten_hierarchy_to_dict(self, data: Dict[str, Any], prefix: str, result: Dict[str, Any]):
        """Flatten hierarchical structure to flat dictionary format."""
        
        for key, value in data.items():
            try:
                # Ensure key is string
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                else:
                    key = str(key)
                
                current_path = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    self._flatten_hierarchy_to_dict(value, current_path, result)
                else:
                    # Ensure value is string if bytes
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    
                    result[current_path] = value
                    
            except Exception as e:
                logger.error(f"Error processing key '{key}': {e}")
                raise
    
    def validate_json(self, data: Union[str, Dict, List]) -> Tuple[bool, Union[Dict, List], str]:
        """
        Validate JSON data and return parsed result.
        
        Args:
            data: JSON data (string, dict, or list)
            
        Returns:
            Tuple: (is_valid, parsed_data, error_message)
        """
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data
            
            return True, parsed, ""
            
        except json.JSONDecodeError as e:
            return False, None, f"JSON syntax error: {e}"
        except Exception as e:
            return False, None, f"Validation error: {e}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        return self.stats.copy()
    
    def get_sample_output(self, data: Dict[str, Any], max_depth: int = 3, max_items: int = 5) -> str:
        """
        Generate a formatted sample of the hierarchical structure.
        
        Args:
            data: Hierarchical data
            max_depth: Maximum depth to show
            max_items: Maximum items per level
            
        Returns:
            str: Formatted sample string
        """
        def format_structure(obj, depth=0):
            if depth >= max_depth:
                return "  " * depth + "..."
            
            if isinstance(obj, dict):
                lines = []
                for i, (key, value) in enumerate(obj.items()):
                    if i >= max_items:
                        lines.append("  " * depth + "...")
                        break
                    
                    if isinstance(value, dict):
                        lines.append("  " * depth + f"{key}: {{")
                        lines.append(format_structure(value, depth + 1))
                        lines.append("  " * depth + "}")
                    else:
                        lines.append("  " * depth + f"{key}: {value}")
                
                return "\n".join(lines)
            else:
                return "  " * depth + str(obj)[:100] + ("..." if len(str(obj)) > 100 else "")
        
        return format_structure(data)

class ConversionManager:
    """Manager class for handling conversion operations with Streamlit integration."""
    
    def __init__(self):
        """Initialize conversion manager."""
        self.converter = JSONConverter()
    
    def convert_data(self, data: Union[Dict, List], conversion_type: str) -> Tuple[bool, Any, str]:
        """
        Convert data between formats.
        
        Args:
            data: Input data
            conversion_type: Type of conversion ('to_hierarchy' or 'to_namevalue')
            
        Returns:
            Tuple: (success, result, error_message)
        """
        try:
            if conversion_type == 'to_hierarchy':
                result = self.converter.to_object_hierarchy(data)
                return True, result, ""
            elif conversion_type == 'to_namevalue':
                result = self.converter.to_name_value_pair(data)
                return True, result, ""
            else:
                return False, None, f"Unknown conversion type: {conversion_type}"
                
        except Exception as e:
            return False, None, str(e)
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        return self.converter.get_stats()
    
    def get_sample_output(self, data: Dict[str, Any]) -> str:
        """Get formatted sample output."""
        return self.converter.get_sample_output(data) 