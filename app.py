import streamlit as st
import json
import logging
import yaml
from datetime import datetime
from tools.json_converter import ConversionManager
from tools.metrics_validator import ValidationManager
from tools.metrics_extractor import ExtractionManager

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def clean_bytes_from_result(obj):
    """Recursively convert any bytes in the result to string for JSON serialization."""
    try:
        if isinstance(obj, dict):
            cleaned_dict = {}
            for k, v in obj.items():
                if isinstance(k, bytes):
                    k = k.decode('utf-8', errors='replace')
                else:
                    k = str(k)
                cleaned_dict[k] = clean_bytes_from_result(v)
            return cleaned_dict
        elif isinstance(obj, list):
            return [clean_bytes_from_result(i) for i in obj]
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, (int, float, bool, type(None))):
            return obj
        else:
            return str(obj)
    except Exception as e:
        return str(obj)


def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        'selected_tool': "Welcome",
        'previous_tool': None,
        'input_method': None,
        'json_data': None,
        'conversion_completed': False,
        'conversion_result': None,
        'conversion_stats': None,
        'conversion_sample': None,
        'show_preview': False,
        'show_stats': False,
        'show_sample': False,
        'val_input_method': None,
        'val_json_data': None,
        'selected_config': None,
        'custom_config': None,
        'validation_results': None,
        'validation_completed': False,
        'validation_date': None,
        'ext_input_method': None,
        'ext_json_data': None,
        'extracted_metrics': None,
        'extraction_completed': False,
        'extraction_date': None,
        'viz_input_method': None,
        'viz_json_data': None,
        'search_query': "",
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def clear_all_session_state():
    """Clear all session state and reset to welcome."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state['selected_tool'] = "Welcome"

def back_to_welcome():
    """Reset app to initial state and go to welcome screen."""
    clear_all_session_state()
    # Ensure the tool selector is set to Welcome
    st.session_state['tool_selector'] = "Welcome"  # Set to Welcome text
    st.rerun()


def render_welcome_screen():
    """Render the welcome screen."""
    st.header("🎉 Welcome to JSON Reports Tools")
    st.markdown("""
    This application is designed to help with JSON CPE reports based on Broadband Forum Data Models TR-181 and TR-098.
    
    ### 🛠️ Available Tools:
    
    **🔄 JSON Conversion**
    - Convert between NameValuePair (flat, dot-notation) and ObjectHierarchy (nested JSON) formats
    - Automatic format detection and validation
    - Download converted files with custom names
    - View conversion statistics and structure samples
    - Support for both input methods: file upload and text paste
    
    **✅ Metrics Validation**
    - Validate JSON data against TR-181, TR-098, and FWA standards
    - Support for custom YAML validation rules
    - Wildcard pattern matching (%, *, {i})
    - Detailed validation reports with found/missing metrics
    - Instance counting for wildcard patterns
    - Download validation results in Markdown or JSON format
    - Automatic format detection (NameValuePair/ObjectHierarchy)
    
    **🔍 Metrics Extraction**
    - Extract metric patterns from JSON data with specific instances
    - Convert specific instances to wildcard patterns (*)
    - Automatic categorization by functional groups (up to second level)
    - Generate simple lists, YAML rules, or Markdown documentation
    - Support for both NameValuePair and ObjectHierarchy formats
    - Multiple download options: simple list, YAML rules, documentation
    
    **📊 JSON Visualization**
    - Interactive JSON preview with syntax highlighting
    - Search and filter JSON keys with clear/confirm buttons
    - Display JSON statistics (elements, keys, depth, size)
    - Link to external JSON diagram tools (jsoncrack.com)
    - Real-time filtering and search results
    
    **📋 Configuration Viewer**
    - Browse and view validation rule configurations dynamically
    - Copy patterns for custom validation setups
    - Download configuration files directly
    - View configuration statistics (rules, patterns, file size)
    - Automatic detection of YAML files in config/ directory
    
    ### 🎯 Key Features:
    
    **📥 Flexible Input Methods**
    - File upload for JSON and YAML files
    - Text paste for direct content input
    - Automatic format detection and validation
    
    **📤 Multiple Output Formats**
    - JSON files with custom names
    - YAML configuration rules
    - Markdown documentation
    - Simple text lists
    - Detailed validation reports
    
    **🔄 State Management**
    - Persistent session state across operations
    - Multiple downloads without losing results
    - Explicit control over state reset
    - Previous results preservation
    
    **📊 Advanced Analytics**
    - Conversion statistics and samples
    - Validation metrics and success rates
    - JSON structure analysis
    - Configuration file statistics
    
    ### 🚀 Getting Started:
    1. **Select a tool** from the sidebar
    2. **Choose input method** (file upload or text paste)
    3. **Process your data** with the chosen tool
    4. **Download results** in your preferred format
    5. **Use Reset App** to start fresh when needed
    
    ### 📁 Supported Formats:
    - **NameValuePair**: Flat structure with dot-notation keys (`Device.WiFi.Radio.1.Stats.BytesSent`)
    - **ObjectHierarchy**: Nested JSON object structure
    - **YAML Configurations**: Validation rule definitions
    - **Markdown Reports**: Detailed validation documentation
    - **JSON Reports**: Structured validation results
    
    ### 🔧 Technical Capabilities:
    - **Wildcard Support**: %, *, {i} patterns for flexible matching
    - **Format Detection**: Automatic NameValuePair vs ObjectHierarchy detection
    - **Categorization**: Intelligent grouping by functional domains
    - **Error Handling**: Comprehensive error reporting and validation
    - **Performance**: Efficient processing of large JSON files
    
    ---
    """)


def render_conversion_ui(tool: str):
    """Render the conversion UI for the specified tool."""
    st.header(f"{tool}")
    st.write("Upload a JSON file or paste the content:")
    
    # Input method selection
    st.markdown("### 📥 Choose Input Method")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Upload File", type="primary" if st.session_state.get('input_method') == 'file' else "secondary"):
            st.session_state['input_method'] = 'file'
            st.rerun()
    with col2:
        if st.button("📝 Paste JSON", type="primary" if st.session_state.get('input_method') == 'text' else "secondary"):
            st.session_state['input_method'] = 'text'
            st.rerun()
    
    # Show appropriate input field based on selection
    if st.session_state.get('input_method') == 'file':
        st.markdown("#### 📁 File Upload")
        uploaded_file = st.file_uploader("Select JSON file", type=["json"], key="file_uploader")
        json_text = ""
    elif st.session_state.get('input_method') == 'text':
        st.markdown("#### 📝 JSON Text Input")
        uploaded_file = None
        json_text = st.text_area("Paste your JSON content here", height=200, key="json_text_area")
    else:
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['json_data'] = None
    elif json_text.strip():
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['json_data'] = None
    else:
        json_data = st.session_state.get('json_data', None)
    
    # JSON preview and editing section
    if json_data is not None:
        st.subheader("📋 JSON Preview & Edit")
        
        # Convert back to formatted JSON for editing
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Allow editing
        edited_json = st.text_area(
            "Edit JSON (if needed):",
            value=formatted_json,
            height=400,
            help="You can modify the JSON content here before processing",
            key="json_editor"
        )
        
        # Validate edited JSON
        try:
            edited_data = json.loads(edited_json)
            st.success("✅ JSON is valid")
            json_data = edited_data
            st.session_state['json_data'] = edited_data
        except Exception as e:
            st.error(f"❌ Invalid JSON: {e}")
            st.stop()
    
    # Conversion options
    if json_data is not None:
        st.subheader("⚙️ Conversion Options")
        show_stats = st.checkbox("Show statistics", value=True)
        show_sample = st.checkbox("Show structure sample", value=True)
        show_preview = st.checkbox("Show result preview", value=False)
        convert_btn = st.button("Convert")
    else:
        st.info("Please upload a JSON file or paste JSON content to continue")
        convert_btn = False

    # Handle conversion
    if convert_btn:
        handle_conversion(json_data, tool, show_stats, show_sample, show_preview)


def handle_conversion(json_data: dict, tool: str, show_stats: bool, show_sample: bool, show_preview: bool):
    """Handle the conversion process."""
    if json_data is None:
        st.error("No JSON data available for conversion")
        return
    
    try:
        converter = ConversionManager()
        
        if tool == "Convert to ObjectHierarchy":
            success, result, error = converter.convert_data(json_data, 'to_hierarchy')
            if not success:
                st.error(f"Conversion error: {error}")
                st.stop()
        else:
            success, result, error = converter.convert_data(json_data, 'to_namevalue')
            if not success:
                st.error(f"Conversion error: {error}")
                st.stop()

        # Clean any bytes before JSON serialization
        result = clean_bytes_from_result(result)
        
        # Store results in session state
        st.session_state['conversion_completed'] = True
        st.session_state['conversion_result'] = result
        st.session_state['conversion_stats'] = converter.get_conversion_stats() if show_stats else None
        st.session_state['conversion_sample'] = converter.get_sample_output(result) if show_sample else None
        st.session_state['show_preview'] = show_preview
        st.session_state['show_stats'] = show_stats
        st.session_state['show_sample'] = show_sample
        
        # Display results
        display_conversion_results(result, show_preview, show_stats, show_sample)
        
    except Exception as e:
        st.error(f"Conversion error: {e}")


def display_conversion_results(result: dict, show_preview: bool, show_stats: bool, show_sample: bool):
    """Display conversion results."""
    st.subheader("✅ Conversion Results")
    st.success("Conversion completed successfully!")
    
    # Download section
    st.markdown("### 📥 Download Converted File")
    output_filename = st.text_input("Output filename", value="result.json", key="download_filename")
    
    try:
        download_data = json.dumps(result, indent=2, ensure_ascii=False)
        st.download_button(
            label="⬇️ Download Result",
            data=download_data,
            file_name=output_filename,
            mime="application/json",
            help="Click to download the converted JSON file"
        )
    except Exception as e:
        st.error(f"Error creating download: {e}")
        st.json(result)
    
    # Show preview of result (only if enabled)
    if show_preview:
        st.markdown("### 👀 Result Preview")
        st.info("Here's a preview of your converted data:")
        st.json(result)
    
    # Show statistics
    if show_stats and st.session_state.get('conversion_stats'):
        stats = st.session_state['conversion_stats']
        st.subheader("📊 Conversion Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Keys", stats['total_keys'])
        with col2:
            st.metric("Processed Keys", stats['processed_keys'])
        with col3:
            st.metric("Errors", stats['errors'])
        st.info(f"Conversion type: {stats['conversion_type']}")
    
    # Show sample
    if show_sample and st.session_state.get('conversion_sample'):
        sample_text = st.session_state['conversion_sample']
        st.subheader("📋 Structure Sample")
        st.code(sample_text, language="json")
    
    # Process control buttons
    st.markdown("---")
    st.markdown("### 🔄 Process Control")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Start New Conversion", type="primary"):
            clear_all_session_state()
            st.rerun()
    with col2:
        if st.button("🏠 Back to Welcome", type="secondary"):
            back_to_welcome()


def handle_validation(json_data: dict, selected_config: dict, custom_config: dict, validation_manager: ValidationManager):
    """Handle the validation process."""
    try:
        if selected_config:
            # Use existing configuration
            success, results, error = validation_manager.validate_data(json_data, selected_config['file_path'])
        else:
            # Use custom configuration
            success, results, error = validation_manager.validate_with_custom_config(json_data, custom_config)
        
        if success:
            # Store results in session state
            st.session_state['validation_results'] = results
            st.session_state['validation_completed'] = True
            st.session_state['validation_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Display results
            display_validation_results(results, validation_manager, json_data)
        
        else:
            st.error(f"Validation error: {error}")
    
    except Exception as e:
        st.error(f"Validation failed: {e}")


def display_validation_results(results: dict, validation_manager: ValidationManager, json_data: dict = None):
    """Display validation results."""
    st.markdown("---")
    st.subheader("✅ Validation Results")
    
    # Statistics
    stats = validation_manager.validator.get_validation_stats()
    st.markdown("#### 📊 Validation Statistics")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Expected", stats['total_expected'])
    with col2:
        st.metric("Total Found", stats['total_found'])
    with col3:
        st.metric("Total Missing", stats['total_missing'])
    with col4:
        st.metric("Total Instances", stats['total_instances'])
    with col5:
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
    
    # Found metrics
    if results['found_metrics']:
        st.markdown("#### ✅ Found Metrics")
        found_summary = validation_manager.validator.get_found_metrics_summary()
        st.code(found_summary, language="text")
    
    # Missing metrics
    if results['missing_metrics']:
        st.markdown("#### ❌ Missing Metrics")
        missing_summary = validation_manager.validator.get_missing_metrics_summary()
        st.code(missing_summary, language="text")
    
    # Download report section
    create_validation_download_section(results, stats, validation_manager, json_data)


def create_validation_download_section(results: dict, stats: dict, validation_manager: ValidationManager, json_data: dict = None):
    """Create download section for validation results."""
    try:
        st.markdown("---")
        st.subheader("📥 Download Validation Report")
        
        # Generate report content
        report_content = f"""# Validation Report - {stats['config_name']}

## 📊 Summary Statistics
- **Total Expected Patterns**: {stats['total_expected']}
- **Total Found Patterns**: {stats['total_found']}
- **Total Instances Found**: {stats['total_instances']}
- **Total Missing Patterns**: {stats['total_missing']}
- **Success Rate**: {stats['success_rate']:.1f}%

## ✅ Found Metrics ({len(results['found_metrics'])} patterns)
"""
        
        for metric in results['found_metrics']:
            report_content += f"- **{metric['pattern']}**: {metric['instances_found']} instances\n"
        
        report_content += f"""

## ❌ Missing Metrics ({len(results['missing_metrics'])} patterns)
"""
        
        for metric in results['missing_metrics']:
            report_content += f"- **{metric['pattern']}**\n"
        
        # Safely detect format
        try:
            input_format = validation_manager.validator.detect_format(json_data) if json_data else 'Unknown'
        except Exception as e:
            input_format = 'Unknown (Error detecting format)'
        
        report_content += f"""

## 📋 Configuration Details
- **Configuration**: {stats['config_name']}
- **Validation Date**: {st.session_state.get('validation_date', 'Unknown')}
- **Input Format**: {input_format}

---
*Generated by JSON Reports Tools*
"""
        
        # Download buttons
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📄 Download Markdown Report",
                data=report_content,
                file_name=f"validation_report_{stats['config_name'].replace(' ', '_').lower()}.md",
                mime="text/markdown"
            )
        
        with col2:
            # JSON report
            json_report = {
                "validation_report": {
                    "config_name": stats['config_name'],
                    "summary": {
                        "total_expected": stats['total_expected'],
                        "total_found": stats['total_found'],
                        "total_instances": stats['total_instances'],
                        "total_missing": stats['total_missing'],
                        "success_rate": stats['success_rate']
                    },
                    "found_metrics": results['found_metrics'],
                    "missing_metrics": results['missing_metrics'],
                    "validation_date": st.session_state.get('validation_date', 'Unknown'),
                    "input_format": input_format
                }
            }
            
            st.download_button(
                label="📊 Download JSON Report",
                data=json.dumps(json_report, indent=2, ensure_ascii=False),
                file_name=f"validation_report_{stats['config_name'].replace(' ', '_').lower()}.json",
                mime="application/json"
            )
        
        # Clear validation button
        st.markdown("---")
        if st.button("🔄 Start New Validation", type="primary"):
            # Clear validation state
            keys_to_clear = [
                'val_input_method', 'val_json_data', 'selected_config', 'custom_config',
                'validation_results', 'validation_completed', 'val_file_uploader',
                'val_json_text_area', 'config_selector', 'custom_config_uploader', 'custom_config_text'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
            
    except Exception as e:
        st.error(f"Error creating download section: {e}")
        st.info("Please try again or contact support if the problem persists.")


def render_validation_ui():
    """Render the metrics validation UI."""
    st.header("🔍 Check Metrics")
    st.write("Upload a JSON file or paste the content to validate against metric patterns:")
    
    # Input method selection
    st.markdown("### 📥 Choose Input Method")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Upload File", type="primary" if st.session_state.get('val_input_method') == 'file' else "secondary", key="val_file_btn"):
            st.session_state['val_input_method'] = 'file'
            st.rerun()
    with col2:
        if st.button("📝 Paste JSON", type="primary" if st.session_state.get('val_input_method') == 'text' else "secondary", key="val_text_btn"):
            st.session_state['val_input_method'] = 'text'
            st.rerun()
    
    # Show appropriate input field based on selection
    if st.session_state.get('val_input_method') == 'file':
        st.markdown("#### 📁 File Upload")
        uploaded_file = st.file_uploader("Select JSON file", type=["json"], key="val_file_uploader")
        json_text = ""
    elif st.session_state.get('val_input_method') == 'text':
        st.markdown("#### 📝 JSON Text Input")
        uploaded_file = None
        json_text = st.text_area("Paste your JSON content here", height=200, key="val_json_text_area")
    else:
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['val_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['val_json_data'] = None
    elif json_text.strip():
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['val_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['val_json_data'] = None
    else:
        json_data = st.session_state.get('val_json_data', None)
    
    # JSON preview and editing section
    if json_data is not None:
        st.markdown("---")
        st.subheader("📋 JSON Preview & Edit")
        
        # Convert back to formatted JSON for editing
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Allow editing
        edited_json = st.text_area(
            "Edit JSON (if needed):",
            value=formatted_json,
            height=400,
            help="You can modify the JSON content here before processing",
            key="val_json_editor"
        )
        
        # Validate edited JSON
        try:
            edited_data = json.loads(edited_json)
            st.success("✅ JSON is valid")
            json_data = edited_data
            st.session_state['val_json_data'] = edited_data
        except Exception as e:
            st.error(f"❌ Invalid JSON: {e}")
            st.stop()
    
    if json_data is not None:
        st.markdown("---")
        st.subheader("⚙️ Validation Configuration")
        
        # Initialize validation manager
        validation_manager = ValidationManager()
        available_configs = validation_manager.get_available_configs()
        
        # Configuration options
        config_option = st.radio(
            "Choose configuration:",
            ["Use existing configuration", "Load custom configuration", "Create custom configuration"],
            key="config_option"
        )
        
        selected_config = None
        custom_config = None
        
        if config_option == "Use existing configuration":
            if available_configs:
                config_names = [f"{config['name']} (v{config['version']})" for config in available_configs]
                selected_config_name = st.selectbox(
                    "Select configuration:",
                    config_names,
                    key="config_selector"
                )
                
                # Find selected config
                for config in available_configs:
                    if f"{config['name']} (v{config['version']})" == selected_config_name:
                        selected_config = config
                        break
                
                if selected_config:
                    st.info(f"📋 {selected_config['description']}")
                    
                    # Display configuration content
                    st.markdown("#### 📄 Configuration Content")
                    try:
                        with open(selected_config['file_path'], 'r', encoding='utf-8') as f:
                            config_content = f.read()
                        
                        st.text_area(
                            "Configuration YAML:",
                            value=config_content,
                            height=400,
                            key="validation_config_viewer",
                            help="You can copy and modify this configuration"
                        )
                        
                        # Download config button
                        st.download_button(
                            label="📥 Download Configuration",
                            data=config_content,
                            file_name=selected_config['file_path'].split('/')[-1],
                            mime="text/yaml"
                        )
                        
                    except Exception as e:
                        st.error(f"Error reading configuration file: {e}")
            else:
                st.warning("No configuration files found in config/ directory")
        
        elif config_option == "Load custom configuration":
            uploaded_config = st.file_uploader("Upload YAML configuration file", type=["yaml", "yml"], key="custom_config_uploader")
            if uploaded_config is not None:
                try:
                    custom_config = yaml.safe_load(uploaded_config)
                    st.success(f"✅ Custom configuration loaded: {custom_config.get('name', 'Unknown')}")
                except Exception as e:
                    st.error(f"Error loading custom configuration: {e}")
                    custom_config = None
        
        elif config_option == "Create custom configuration":
            st.markdown("#### 📝 Custom Configuration")
            custom_config_text = st.text_area(
                "Paste your YAML configuration:",
                height=300,
                placeholder="# Custom validation rules\nname: 'Custom Rules'\ndescription: 'Custom metric validation'\nversion: '1.0'\nrules:\n  - name: 'Example Rule'\n    description: 'Example metrics'\n    category: 'Example'\n    patterns:\n      - 'Device.Example.%.Metric'",
                key="custom_config_text"
            )
            
            if custom_config_text.strip():
                try:
                    custom_config = yaml.safe_load(custom_config_text)
                    st.success("✅ Custom configuration parsed successfully")
                except Exception as e:
                    st.error(f"Error parsing custom configuration: {e}")
                    custom_config = None
        
        # Validation button
        if selected_config or custom_config:
            st.markdown("### 🔍 Start Validation")
            validate_btn = st.button("🔍 Validate Metrics", type="primary")
            
            if validate_btn:
                handle_validation(json_data, selected_config, custom_config, validation_manager)
        
        else:
            st.info("Please select or create a validation configuration")
    else:
        st.info("Please upload a JSON file or paste JSON content to validate")


def handle_extraction(json_data: dict, extraction_manager: ExtractionManager):
    """Handle the extraction process."""
    try:
        # Extract metrics
        success, metrics, error = extraction_manager.extract_metrics(json_data)
        
        if success:
            # Store results in session state
            st.session_state['extracted_metrics'] = metrics
            st.session_state['extraction_completed'] = True
            st.session_state['extraction_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.rerun()
        
        else:
            st.error(f"Extraction failed: {error}")
    
    except Exception as e:
        st.error(f"Extraction error: {e}")


def show_extraction_results():
    """Show extraction results."""
    if st.session_state.get('extraction_completed', False):
        st.markdown("---")
        st.subheader("✅ Extraction Results")
        
        # Get stored results
        metrics = st.session_state.get('extracted_metrics', [])
        extraction_date = st.session_state.get('extraction_date', 'Unknown')
        
        if metrics:
            # Statistics
            st.markdown("#### 📊 Extraction Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Metrics", len(metrics))
            with col2:
                extraction_manager = ExtractionManager()
                categories = extraction_manager.categorize_metrics(metrics)
                st.metric("Categories", len(categories))
            with col3:
                st.metric("Extraction Date", extraction_date)
            
            # Show metrics by category
            st.markdown("#### 📋 Extracted Metrics by Category")
            for category, patterns in categories.items():
                with st.expander(f"📁 {category} ({len(patterns)} metrics)"):
                    for pattern in sorted(patterns):
                        st.code(pattern, language="text")
            
            # Download options
            create_extraction_download_section(metrics, extraction_manager)


def create_extraction_download_section(metrics: list, extraction_manager: ExtractionManager):
    """Create download section for extraction results."""
    st.markdown("---")
    st.subheader("📥 Download Options")
    
    # Configuration name
    config_name = st.text_input("Configuration name", value="Extracted_Metrics", key="config_name_input")
    
    # Download buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Simple list
        simple_list = extraction_manager.generate_simple_list(metrics)
        st.download_button(
            label="📄 Download Simple List",
            data=simple_list,
            file_name=f"{config_name.lower()}_metrics.txt",
            mime="text/plain"
        )
    
    with col2:
        # YAML rules
        yaml_rules = extraction_manager.generate_yaml_rules(metrics, config_name)
        st.download_button(
            label="⚙️ Export YAML Rules",
            data=yaml_rules,
            file_name=f"{config_name.lower()}_rules.yaml",
            mime="text/yaml"
        )
    
    with col3:
        # Markdown documentation
        markdown_doc = extraction_manager.generate_markdown_doc(metrics, config_name)
        st.download_button(
            label="📚 Generate Documentation",
            data=markdown_doc,
            file_name=f"{config_name.lower()}_metrics.md",
            mime="text/markdown"
        )
    
    # Clear extraction button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Extraction", type="primary"):
            # Clear extraction state
            keys_to_clear = [
                'ext_input_method', 'ext_json_data', 'extracted_metrics',
                'extraction_completed', 'extraction_date', 'ext_file_uploader',
                'ext_json_text_area', 'config_name_input'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Welcome", type="secondary"):
            back_to_welcome()


def render_extraction_ui():
    """Render the metrics extraction UI."""
    st.header("🔍 Extract Metrics")
    st.write("Upload a JSON file or paste the content to extract metric patterns:")
    
    # Input method selection
    st.markdown("### 📥 Choose Input Method")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Upload File", type="primary" if st.session_state.get('ext_input_method') == 'file' else "secondary", key="ext_file_btn"):
            st.session_state['ext_input_method'] = 'file'
            st.rerun()
    with col2:
        if st.button("📝 Paste JSON", type="primary" if st.session_state.get('ext_input_method') == 'text' else "secondary", key="ext_text_btn"):
            st.session_state['ext_input_method'] = 'text'
            st.rerun()
    
    # Show appropriate input field based on selection
    if st.session_state.get('ext_input_method') == 'file':
        st.markdown("#### 📁 File Upload")
        uploaded_file = st.file_uploader("Select JSON file", type=["json"], key="ext_file_uploader")
        json_text = ""
    elif st.session_state.get('ext_input_method') == 'text':
        st.markdown("#### 📝 JSON Text Input")
        uploaded_file = None
        json_text = st.text_area("Paste your JSON content here", height=200, key="ext_json_text_area")
    else:
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['ext_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['ext_json_data'] = None
    elif json_text.strip():
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['ext_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['ext_json_data'] = None
    else:
        json_data = st.session_state.get('ext_json_data', None)
    
    # JSON preview and editing section
    if json_data is not None:
        st.markdown("---")
        st.subheader("📋 JSON Preview & Edit")
        
        # Convert back to formatted JSON for editing
        formatted_json = json.dumps(json_data, indent=2, ensure_ascii=False)
        
        # Allow editing
        edited_json = st.text_area(
            "Edit JSON (if needed):",
            value=formatted_json,
            height=400,
            help="You can modify the JSON content here before processing",
            key="ext_json_editor"
        )
        
        # Validate edited JSON
        try:
            edited_data = json.loads(edited_json)
            st.success("✅ JSON is valid")
            json_data = edited_data
            st.session_state['ext_json_data'] = edited_data
        except Exception as e:
            st.error(f"❌ Invalid JSON: {e}")
            st.stop()
    
    if json_data is not None:
        st.markdown("---")
        st.subheader("🔍 Extract Metrics")
        
        # Initialize extraction manager
        extraction_manager = ExtractionManager()
        
        # Extract button
        extract_btn = st.button("🔍 Extract Metrics", type="primary")
        
        if extract_btn:
            handle_extraction(json_data, extraction_manager)
        
        else:
            st.info("Click 'Extract Metrics' to start the extraction process")
    
    # Show extraction results
    show_extraction_results()


def display_filtered_json(json_data: dict, search_query: str):
    """Display filtered JSON data."""
    # Filter data based on search query
    def filter_json_data(data, query):
        """Filter JSON data based on search query."""
        if not query.strip():
            return data
        
        query = query.lower()
        filtered_data = {}
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    # Check if key contains the search query
                    if query in key.lower():
                        if path:
                            # Create nested structure
                            parts = path.split('.')
                            current = filtered_data
                            for part in parts:
                                if part not in current:
                                    current[part] = {}
                                current = current[part]
                            current[key] = value
                        else:
                            filtered_data[key] = value
                    # Continue searching in nested objects
                    if isinstance(value, (dict, list)):
                        search_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    current_path = f"{path}[{i}]"
                    if isinstance(item, (dict, list)):
                        search_recursive(item, current_path)
        
        search_recursive(data)
        return filtered_data
    
    # Apply search filter
    display_data = filter_json_data(json_data, search_query)
    
    # Show search results info
    if search_query.strip():
        if display_data:
            st.success(f"✅ Found {len(display_data)} matching keys for '{search_query}'")
        else:
            st.error(f"❌ No keys found matching '{search_query}'")
            st.info("💡 Try a different search term or check the spelling")
    else:
        st.info("📋 Showing complete JSON structure")
    
    # Display options
    st.markdown("### 📊 Display Options")
    col1, col2 = st.columns(2)
    with col1:
        show_stats = st.checkbox("Show JSON statistics", value=True)
    with col2:
        expand_all = st.checkbox("Expand all levels", value=False)
    
    # Show JSON statistics
    if show_stats:
        display_json_statistics(display_data)
    
    # Display JSON with search highlighting
    st.markdown("#### 📋 JSON Structure")
    
    if search_query.strip() and display_data:
        st.info(f"Showing filtered results for '{search_query}'. Use the search box above to modify the filter.")
    
    # Format JSON for display
    formatted_json = json.dumps(display_data, indent=2, ensure_ascii=False)
    
    # Display with syntax highlighting
    st.code(formatted_json, language="json")


def display_json_statistics(data: dict):
    """Display JSON statistics."""
    st.markdown("#### 📈 JSON Statistics")
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    def count_elements(obj):
        """Count total elements in JSON structure."""
        if isinstance(obj, dict):
            return 1 + sum(count_elements(v) for v in obj.values())
        elif isinstance(obj, list):
            return 1 + sum(count_elements(item) for item in obj)
        else:
            return 1
    
    def count_keys(obj):
        """Count total keys in JSON structure."""
        if isinstance(obj, dict):
            return len(obj) + sum(count_keys(v) for v in obj.values())
        elif isinstance(obj, list):
            return sum(count_keys(item) for item in obj)
        else:
            return 0
    
    def get_max_depth(obj, depth=0):
        """Get maximum depth of JSON structure."""
        if isinstance(obj, dict):
            return max([get_max_depth(v, depth + 1) for v in obj.values()], default=depth)
        elif isinstance(obj, list):
            return max([get_max_depth(item, depth + 1) for item in obj], default=depth)
        else:
            return depth
    
    total_elements = count_elements(data)
    total_keys = count_keys(data)
    max_depth = get_max_depth(data)
    data_size = len(json.dumps(data, indent=2))
    
    with stats_col1:
        st.metric("Total Elements", total_elements)
    with stats_col2:
        st.metric("Total Keys", total_keys)
    with stats_col3:
        st.metric("Max Depth", max_depth)
    with stats_col4:
        st.metric("Size (chars)", f"{data_size:,}")


def render_visualization_ui():
    """Render the JSON visualization UI."""
    st.header("🔍 JSON Visualizer")
    st.write("Upload a JSON file or paste the content to visualize and search:")
    
    # Input method selection
    st.markdown("### 📥 Choose Input Method")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📁 Upload File", type="primary" if st.session_state.get('viz_input_method') == 'file' else "secondary", key="viz_file_btn"):
            st.session_state['viz_input_method'] = 'file'
            st.rerun()
    with col2:
        if st.button("📝 Paste JSON", type="primary" if st.session_state.get('viz_input_method') == 'text' else "secondary", key="viz_text_btn"):
            st.session_state['viz_input_method'] = 'text'
            st.rerun()
    
    # Show appropriate input field based on selection
    if st.session_state.get('viz_input_method') == 'file':
        st.markdown("#### 📁 File Upload")
        uploaded_file = st.file_uploader("Select JSON file", type=["json"], key="viz_file_uploader")
        json_text = ""
    elif st.session_state.get('viz_input_method') == 'text':
        st.markdown("#### 📝 JSON Text Input")
        uploaded_file = None
        json_text = st.text_area("Paste your JSON content here", height=200, key="viz_json_text_area")
    else:
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['viz_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['viz_json_data'] = None
    elif json_text.strip():
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['viz_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['viz_json_data'] = None
    else:
        json_data = st.session_state.get('viz_json_data', None)
    
    if json_data is not None:
        st.markdown("---")
        st.subheader("🔍 JSON Visualization & Search")
        
        # Search functionality
        st.markdown("### 🔎 Search Keys")
        search_query = st.text_input(
            "Search for keys (optional):",
            value=st.session_state.get('search_query', ""),
            placeholder="Enter key name to filter (e.g., 'Device', 'WiFi', 'Status')",
            help="Leave empty to show all keys",
            key="search_input"
        )
        
        # Search buttons side by side
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Search", type="primary"):
                st.session_state['search_query'] = search_query
                st.rerun()
        with col2:
            if st.button("❌ Clear", type="secondary"):
                st.session_state['search_query'] = ""
                st.rerun()
        
        # Use the current search query
        current_search = st.session_state.get('search_query', "")
        
        # Filter and display data
        display_filtered_json(json_data, current_search)
        
        # Clear visualization button
        st.markdown("---")
        if st.button("🔄 Load New JSON", type="primary"):
            # Clear visualization state
            keys_to_clear = [
                'viz_input_method', 'viz_json_data', 'search_query',
                'viz_file_uploader', 'viz_json_text_area'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # JSON Crack link
        st.markdown("---")
        st.markdown("### 📊 JSON Diagram Tool")
        st.markdown("For JSON diagram visualization, use the following link:")
        st.markdown("[🔗 JSON Crack Editor](https://jsoncrack.com/editor)")
        st.info("💡 Copy your JSON data and paste it in JSON Crack for interactive diagram visualization")
    else:
        st.info("Please upload a JSON file or paste JSON content to visualize")


def main():
    """Main application function."""
    st.set_page_config(page_title="Json Reports Tools", layout="wide")
    
    # Initialize session state
    initialize_session_state()
    
    # Create sidebar
    st.sidebar.title("🧰 Json Reports Tools")
    
    # Tool selection
    tool = st.sidebar.radio(
        "Select a tool:",
        (
            "Welcome",
            "Convert to NameValuePair",
            "Convert to ObjectHierarchy",
            "Check Metrics",
            "Extract Metrics",
            "Visualize"
        ),
        key='tool_selector'
    )
    
    # Update selected tool
    st.session_state['selected_tool'] = tool
    
    st.sidebar.markdown("---")
    
    # Reset app button
    if st.sidebar.button("🔄 Reset App"):
        clear_all_session_state()
        st.rerun()
    
    st.title("📘 Json Reports Tools")
    
    # Main panel logic
    if tool == "Welcome":
        render_welcome_screen()
    elif tool in ["Convert to NameValuePair", "Convert to ObjectHierarchy"]:
        render_conversion_ui(tool)
    elif tool == "Check Metrics":
        render_validation_ui()
    elif tool == "Extract Metrics":
        render_extraction_ui()
    elif tool == "Visualize":
        render_visualization_ui()


if __name__ == "__main__":
    main() 