import streamlit as st
import json
import logging
import yaml
from datetime import datetime
from tools.json_converter import ConversionManager
from tools.metrics_validator import ValidationManager
from tools.metrics_extractor import ExtractionManager

# Configure logging for the app
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

def clean_bytes_from_result(obj):
    """Recursively convert any bytes in the result to string for JSON serialization."""
    try:
        if isinstance(obj, dict):
            cleaned_dict = {}
            for k, v in obj.items():
                # Clean key - ensure it's string
                if isinstance(k, bytes):
                    k = k.decode('utf-8', errors='replace')
                else:
                    k = str(k)
                # Clean value
                cleaned_dict[k] = clean_bytes_from_result(v)
            return cleaned_dict
        elif isinstance(obj, list):
            return [clean_bytes_from_result(i) for i in obj]
        elif isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, (int, float, bool, type(None))):
            return obj
        else:
            # Convert anything else to string
            return str(obj)
    except Exception as e:
        # If anything fails, convert to string
        return str(obj)

def clear_conversion_state():
    """Clear all conversion-related session state."""
    keys_to_clear = [
        'conversion_completed',
        'conversion_result',
        'conversion_stats',
        'conversion_sample',
        'show_preview',
        'show_stats',
        'show_sample',
        'uploaded_file', 
        'input_method',
        'json_data',
        'file_uploader',
        'json_text_area',
        'json_editor',
        'download_filename',
        'download_filename_prev'
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

st.set_page_config(page_title="Json Reports Tools", layout="wide")

# Sidebar
st.sidebar.title("🧰 Json Reports Tools")

# Initialize session state for tool selection
if 'selected_tool' not in st.session_state:
    st.session_state['selected_tool'] = "Welcome"

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
    key='tool_selector',
    index=0 if st.session_state['selected_tool'] == "Welcome" else None
)

# Check if tool changed and reset panel
if 'previous_tool' not in st.session_state:
    st.session_state['previous_tool'] = tool
elif st.session_state['previous_tool'] != tool:
    # Tool changed, reset panel
    st.session_state['previous_tool'] = tool
    # Clear all session state
    if 'conversion_completed' in st.session_state:
        del st.session_state['conversion_completed']
    if 'uploaded_file' in st.session_state:
        del st.session_state['uploaded_file']
    if 'input_method' in st.session_state:
        del st.session_state['input_method']
    if 'json_data' in st.session_state:
        del st.session_state['json_data']
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset App"):
    # Clear ALL session state completely
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Set initial state
    st.session_state['selected_tool'] = "Welcome"
    st.rerun()
# Config Versions section
st.sidebar.markdown("### 📋 Config Versions")

# Dynamically read config files from config/ directory
import os
config_dir = "config"
config_files = []

if os.path.exists(config_dir):
    for file in os.listdir(config_dir):
        if file.endswith('.yaml') or file.endswith('.yml'):
            # Create display name from filename
            display_name = file.replace('_', ' ').replace('.yaml', '').replace('.yml', '').title()
            config_files.append((file, display_name))

selected_config = st.sidebar.selectbox(
    "Select configuration to view:",
    options=[None] + [f[0] for f in config_files],
    format_func=lambda x: "Choose a config..." if x is None else x
)

st.title("📘 Json Reports Tools")

# Main panel
if selected_config:
    # Show configuration content in main panel
    st.header(f"📄 Configuration: {selected_config}")
    
    config_path = f"config/{selected_config}"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # Display file info
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**File:** {selected_config}")
        with col2:
            st.download_button(
                label="📥 Download Config",
                data=config_content,
                file_name=selected_config,
                mime="text/yaml"
            )
        
        # Display content in main panel
        st.subheader("Configuration Content")
        st.text_area(
            "YAML Configuration:",
            value=config_content,
            height=600,
            key=f"config_viewer_main_{selected_config}",
            help="You can copy sections from this configuration for use in validation tools"
        )
        
        # Show statistics
        st.subheader("📊 Configuration Statistics")
        try:
            import yaml
            config_data = yaml.safe_load(config_content)
            if config_data and 'rules' in config_data:
                total_rules = len(config_data['rules'])
                total_patterns = sum(len(rule.get('patterns', [])) for rule in config_data['rules'])
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Rules", total_rules)
                with col2:
                    st.metric("Total Patterns", total_patterns)
                with col3:
                    st.metric("File Size", f"{len(config_content)} chars")
            else:
                st.warning("Configuration file doesn't have the expected structure")
        except yaml.YAMLError:
            st.error("Invalid YAML format in configuration file")
            
    except FileNotFoundError:
        st.error(f"Configuration file {selected_config} not found")
    except Exception as e:
        st.error(f"Error reading configuration: {e}")

elif tool in ["Convert to NameValuePair", "Convert to ObjectHierarchy"]:
    st.header(f"{tool}")
    st.write("Upload a JSON file or paste the content:")
    
    # Initialize session state for input method
    if 'input_method' not in st.session_state:
        st.session_state['input_method'] = None
    if 'json_data' not in st.session_state:
        st.session_state['json_data'] = None
    
    # Input method selection
    st.markdown("### 📥 Choose Input Method")
    if st.button("📁 Upload File", type="primary" if st.session_state.get('input_method') == 'file' else "secondary"):
        st.session_state['input_method'] = 'file'
        st.rerun()
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
        # No method selected yet
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # JSON preview and editing section
    json_data = None
    
    # Determine input method and load data
    if uploaded_file is not None:
        # File was uploaded
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['json_data'] = None
    elif json_text.strip():
        # Text was entered
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['json_data'] = None
    else:
        # No input yet
        json_data = st.session_state.get('json_data', None)
    
    # Preview and edit section
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
            json_data = edited_data  # Use edited version
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

    # Check if convert button was clicked
    if convert_btn:
        if json_data is None:
            st.error("No JSON data available for conversion")
            logger.error("No JSON data available for conversion")
        else:
            try:
                converter = ConversionManager()
                
                if tool == "Convert to ObjectHierarchy":
                    # NameValuePair -> ObjectHierarchy
                    success, result, error = converter.convert_data(json_data, 'to_hierarchy')
                    if not success:
                        logger.error(f"Conversion failed: {error}")
                        st.error(f"Conversion error: {error}")
                        st.stop()
                else:
                    # ObjectHierarchy -> NameValuePair
                    success, result, error = converter.convert_data(json_data, 'to_namevalue')
                    if not success:
                        logger.error(f"Conversion failed: {error}")
                        st.error(f"Conversion error: {error}")
                        st.stop()

                # Clean any bytes before JSON serialization
                result = clean_bytes_from_result(result)
                
                # Mark conversion as completed and store result
                st.session_state['conversion_completed'] = True
                st.session_state['conversion_result'] = result
                st.session_state['conversion_stats'] = converter.get_conversion_stats() if show_stats else None
                st.session_state['conversion_sample'] = converter.get_sample_output(result) if show_sample else None
                st.session_state['show_preview'] = show_preview
                st.session_state['show_stats'] = show_stats
                st.session_state['show_sample'] = show_sample
                
                # Display results section
                st.subheader("✅ Conversion Results")
                st.success("Conversion completed successfully!")
                
                # Download section with filename input
                st.markdown("### 📥 Download Converted File")
                
                # Filename input after conversion
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
                    logger.error(f"Error creating download data: {e}")
                    st.error(f"Error creating download: {e}")
                    # Still show the result even if download fails
                    st.json(result)
                
                # Show preview of result (only if enabled)
                if show_preview:
                    st.markdown("### 👀 Result Preview")
                    st.info("Here's a preview of your converted data:")
                    st.json(result)
                
                if show_stats:
                    stats = converter.get_conversion_stats()
                    st.subheader("📊 Conversion Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Keys", stats['total_keys'])
                    with col2:
                        st.metric("Processed Keys", stats['processed_keys'])
                    with col3:
                        st.metric("Errors", stats['errors'])
                    
                    st.info(f"Conversion type: {stats['conversion_type']}")
                
                if show_sample:
                    sample_text = converter.get_sample_output(result)
                    st.subheader("📋 Structure Sample")
                    st.code(sample_text, language="json")
                
                # End process section
                st.markdown("---")
                st.markdown("### 🔄 Process Control")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📁 Start New Conversion", type="primary"):
                        # Clear all session state and rerun
                        clear_conversion_state()
                        st.rerun()
                with col2:
                    if st.button("🏠 Back to Welcome", type="secondary"):
                        st.session_state['selected_tool'] = "Welcome"
                        # Clear conversion-related session state
                        clear_conversion_state()
                        st.rerun()
                    
            except Exception as e:
                logger.error(f"Exception during conversion: {e}")
                st.error(f"Conversion error: {e}")

    
    # Show results if conversion was already completed (but not immediately after conversion)
    if st.session_state.get('conversion_completed', False) and not convert_btn:
        st.markdown("---")
        st.subheader("✅ Previous Conversion Results")
        st.info("Your previous conversion results are still available below.")
        
        # Get stored results
        result = st.session_state.get('conversion_result')
        show_preview = st.session_state.get('show_preview', False)
        show_stats = st.session_state.get('show_stats', False)
        show_sample = st.session_state.get('show_sample', False)
        
        if result is not None:
            # Download section
            st.markdown("### 📥 Download Converted File")
            output_filename = st.text_input("Output filename", value="result.json", key="download_filename_prev")
            
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
            
            # Show preview if enabled
            if show_preview:
                st.markdown("### 👀 Result Preview")
                st.info("Here's a preview of your converted data:")
                st.json(result)
            
            # Show stats if enabled
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
            
            # Show sample if enabled
            if show_sample and st.session_state.get('conversion_sample'):
                sample_text = st.session_state['conversion_sample']
                st.subheader("📋 Structure Sample")
                st.code(sample_text, language="json")
            
            # Process control buttons
            st.markdown("---")
            st.markdown("### 🔄 Process Control")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📁 Start New Conversion", type="primary", key="new_conv_prev"):
                    # Clear all session state and rerun
                    clear_conversion_state()
                    st.rerun()
            with col2:
                if st.button("🏠 Back to Welcome", type="secondary", key="back_welcome_prev"):
                    st.session_state['selected_tool'] = "Welcome"
                    # Clear conversion-related session state
                    clear_conversion_state()
                    st.rerun()

elif tool == "Welcome":
    # Welcome screen
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

elif tool == "Check Metrics":
    st.header("🔍 Check Metrics")
    st.write("Upload a JSON file or paste the content to validate against metric patterns:")
    
    # Initialize session state for validation
    if 'val_input_method' not in st.session_state:
        st.session_state['val_input_method'] = None
    if 'val_json_data' not in st.session_state:
        st.session_state['val_json_data'] = None
    if 'selected_config' not in st.session_state:
        st.session_state['selected_config'] = None
    if 'custom_config' not in st.session_state:
        st.session_state['custom_config'] = None
    
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
        # No method selected yet
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        # File was uploaded
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['val_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['val_json_data'] = None
    elif json_text.strip():
        # Text was entered
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['val_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['val_json_data'] = None
    else:
        # No input yet
        json_data = st.session_state.get('val_json_data', None)
    
    # Configuration selection
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
                        
                        report_content += f"""

## 📋 Configuration Details
- **Configuration**: {stats['config_name']}
- **Validation Date**: {st.session_state.get('validation_date', 'Unknown')}
- **Input Format**: {validation_manager.validator.detect_format(json_data)}

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
                                    "input_format": validation_manager.validator.detect_format(json_data)
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
                                'val_input_method',
                                'val_json_data',
                                'selected_config',
                                'custom_config',
                                'validation_results',
                                'validation_completed',
                                'val_file_uploader',
                                'val_json_text_area',
                                'config_selector',
                                'custom_config_uploader',
                                'custom_config_text'
                            ]
                            for key in keys_to_clear:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()
                    
                    else:
                        st.error(f"Validation error: {error}")
                
                except Exception as e:
                    st.error(f"Validation failed: {e}")
        
        else:
            st.info("Please select or create a validation configuration")
    
    else:
        st.info("Please upload a JSON file or paste JSON content to validate")

elif tool == "Extract Metrics":
    st.header("🔍 Extract Metrics")
    st.write("Upload a JSON file or paste the content to extract metric patterns:")
    
    # Initialize session state for extraction
    if 'ext_input_method' not in st.session_state:
        st.session_state['ext_input_method'] = None
    if 'ext_json_data' not in st.session_state:
        st.session_state['ext_json_data'] = None
    if 'extracted_metrics' not in st.session_state:
        st.session_state['extracted_metrics'] = None
    
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
        # No method selected yet
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        # File was uploaded
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['ext_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['ext_json_data'] = None
    elif json_text.strip():
        # Text was entered
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['ext_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['ext_json_data'] = None
    else:
        # No input yet
        json_data = st.session_state.get('ext_json_data', None)
    
    # Extract metrics
    if json_data is not None:
        st.markdown("---")
        st.subheader("🔍 Extract Metrics")
        
        # Initialize extraction manager
        extraction_manager = ExtractionManager()
        
        # Extract button
        extract_btn = st.button("🔍 Extract Metrics", type="primary")
        
        if extract_btn:
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
        
        else:
            st.info("Click 'Extract Metrics' to start the extraction process")
    
    # Show extraction results (either from current extraction or previous)
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
                        'ext_input_method',
                        'ext_json_data',
                        'extracted_metrics',
                        'extraction_completed',
                        'extraction_date',
                        'ext_file_uploader',
                        'ext_json_text_area',
                        'config_name_input'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            
            with col2:
                if st.button("🏠 Back to Welcome", type="secondary"):
                    # Clear all extraction state and go to welcome
                    keys_to_clear = [
                        'ext_input_method',
                        'ext_json_data',
                        'extracted_metrics',
                        'extraction_completed',
                        'extraction_date',
                        'ext_file_uploader',
                        'ext_json_text_area',
                        'config_name_input',
                        'selected_tool'
                    ]
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state['selected_tool'] = "Welcome"
                    st.rerun()
    
    elif json_data is None:
        st.info("Please upload a JSON file or paste JSON content to extract metrics")

elif tool == "Visualize":
    st.header("🔍 JSON Visualizer")
    st.write("Upload a JSON file or paste the content to visualize and search:")
    
    # Initialize session state for visualization
    if 'viz_input_method' not in st.session_state:
        st.session_state['viz_input_method'] = None
    if 'viz_json_data' not in st.session_state:
        st.session_state['viz_json_data'] = None
    if 'search_query' not in st.session_state:
        st.session_state['search_query'] = ""
    
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
        # No method selected yet
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load JSON data
    json_data = None
    
    if uploaded_file is not None:
        # File was uploaded
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state['viz_json_data'] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state['viz_json_data'] = None
    elif json_text.strip():
        # Text was entered
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state['viz_json_data'] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state['viz_json_data'] = None
    else:
        # No input yet
        json_data = st.session_state.get('viz_json_data', None)
    
    # Visualization and search section
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
        display_data = filter_json_data(json_data, current_search)
        
        # Show search results info
        if current_search.strip():
            if display_data:
                st.success(f"✅ Found {len(display_data)} matching keys for '{current_search}'")
            else:
                st.error(f"❌ No keys found matching '{current_search}'")
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
            
            total_elements = count_elements(display_data)
            total_keys = count_keys(display_data)
            max_depth = get_max_depth(display_data)
            data_size = len(json.dumps(display_data, indent=2))
            
            with stats_col1:
                st.metric("Total Elements", total_elements)
            with stats_col2:
                st.metric("Total Keys", total_keys)
            with stats_col3:
                st.metric("Max Depth", max_depth)
            with stats_col4:
                st.metric("Size (chars)", f"{data_size:,}")
        
        # Display JSON with search highlighting
        st.markdown("#### 📋 JSON Structure")
        
        if current_search.strip() and display_data:
            st.info(f"Showing filtered results for '{current_search}'. Use the search box above to modify the filter.")
        
        # Format JSON for display
        formatted_json = json.dumps(display_data, indent=2, ensure_ascii=False)
        
        # Display with syntax highlighting
        st.code(formatted_json, language="json")
        
        # Clear visualization button
        st.markdown("---")
        if st.button("🔄 Load New JSON", type="primary"):
            # Clear visualization state
            keys_to_clear = [
                'viz_input_method',
                'viz_json_data',
                'search_query',
                'viz_file_uploader',
                'viz_json_text_area'
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