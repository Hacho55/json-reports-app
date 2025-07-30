"""
UI Helpers for Streamlit application
Provides common functions for session state management and UI components
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple


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


def clear_session_state(keys: list):
    """Clear specific session state keys."""
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def clear_all_session_state():
    """Clear all session state and reset to welcome."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state['selected_tool'] = "Welcome"


def handle_tool_change(current_tool: str):
    """Handle tool selection changes."""
    if 'previous_tool' not in st.session_state:
        st.session_state['previous_tool'] = current_tool
    elif st.session_state['previous_tool'] != current_tool:
        st.session_state['previous_tool'] = current_tool
        # Clear tool-specific state when tool changes
        clear_session_state([
            'conversion_completed', 'uploaded_file', 'input_method', 'json_data',
            'val_input_method', 'val_json_data', 'selected_config', 'custom_config',
            'ext_input_method', 'ext_json_data', 'extracted_metrics',
            'viz_input_method', 'viz_json_data', 'search_query'
        ])


def create_input_method_selector(prefix: str = "") -> str:
    """Create input method selection buttons.
    
    Args:
        prefix: Prefix for session state keys (e.g., 'val_', 'ext_', 'viz_')
    
    Returns:
        Selected input method ('file' or 'text')
    """
    input_method_key = f"{prefix}input_method"
    
    st.markdown("### 📥 Choose Input Method")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Upload File", 
                    type="primary" if st.session_state.get(input_method_key) == 'file' else "secondary",
                    key=f"{prefix}file_btn"):
            st.session_state[input_method_key] = 'file'
            st.rerun()
    
    with col2:
        if st.button("📝 Paste JSON", 
                    type="primary" if st.session_state.get(input_method_key) == 'text' else "secondary",
                    key=f"{prefix}text_btn"):
            st.session_state[input_method_key] = 'text'
            st.rerun()
    
    return st.session_state.get(input_method_key)


def load_json_data(prefix: str = "") -> Optional[Dict]:
    """Load JSON data from file upload or text input.
    
    Args:
        prefix: Prefix for session state keys
    
    Returns:
        Loaded JSON data or None
    """
    input_method = st.session_state.get(f"{prefix}input_method")
    json_data_key = f"{prefix}json_data"
    
    if input_method == 'file':
        st.markdown("#### 📁 File Upload")
        uploaded_file = st.file_uploader("Select JSON file", type=["json"], 
                                       key=f"{prefix}file_uploader")
        json_text = ""
    elif input_method == 'text':
        st.markdown("#### 📝 JSON Text Input")
        uploaded_file = None
        json_text = st.text_area("Paste your JSON content here", height=200, 
                               key=f"{prefix}json_text_area")
    else:
        st.info("👆 Please select an input method above")
        uploaded_file = None
        json_text = ""
    
    # Load data
    json_data = None
    
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            st.success(f"✅ File loaded: {uploaded_file.name}")
            st.session_state[json_data_key] = json_data
        except Exception as e:
            st.error(f"Error loading file: {e}")
            json_data = None
            st.session_state[json_data_key] = None
    elif json_text.strip():
        try:
            json_data = json.loads(json_text)
            st.success("✅ JSON content loaded from text area")
            st.session_state[json_data_key] = json_data
        except Exception as e:
            st.error(f"Error parsing JSON: {e}")
            json_data = None
            st.session_state[json_data_key] = None
    else:
        json_data = st.session_state.get(json_data_key, None)
    
    return json_data


def create_json_editor(json_data: Dict) -> Dict:
    """Create JSON editor for preview and editing.
    
    Args:
        json_data: JSON data to edit
    
    Returns:
        Edited JSON data
    """
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
        return edited_data
    except Exception as e:
        st.error(f"❌ Invalid JSON: {e}")
        st.stop()


def create_download_section(data: Any, filename: str, mime_type: str = "application/json"):
    """Create download section with filename input and download button.
    
    Args:
        data: Data to download
        filename: Default filename
        mime_type: MIME type for download
    """
    st.markdown("### 📥 Download Converted File")
    
    output_filename = st.text_input("Output filename", value=filename, key="download_filename")
    
    try:
        if isinstance(data, dict):
            download_data = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            download_data = str(data)
        
        st.download_button(
            label="⬇️ Download Result",
            data=download_data,
            file_name=output_filename,
            mime=mime_type,
            help="Click to download the file"
        )
        
    except Exception as e:
        st.error(f"Error creating download: {e}")
        if isinstance(data, dict):
            st.json(data)


def create_process_control_buttons():
    """Create process control buttons (Start New / Back to Welcome)."""
    st.markdown("---")
    st.markdown("### 🔄 Process Control")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📁 Start New Process", type="primary"):
            clear_all_session_state()
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Welcome", type="secondary"):
            st.session_state['selected_tool'] = "Welcome"
            clear_all_session_state()
            st.rerun()


def create_sidebar():
    """Create the sidebar with tool selection and config viewer."""
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
        key='tool_selector',
        index=0 if st.session_state['selected_tool'] == "Welcome" else None
    )
    
    # Handle tool change
    handle_tool_change(tool)
    
    st.sidebar.markdown("---")
    
    # Reset app button
    if st.sidebar.button("🔄 Reset App"):
        clear_all_session_state()
        st.rerun()
    
    # Config Versions section
    selected_config = create_config_viewer()
    
    return tool, selected_config


def create_config_viewer():
    """Create the configuration viewer in sidebar."""
    st.sidebar.markdown("### 📋 Config Versions")
    
    import os
    config_dir = "config"
    config_files = []
    
    if os.path.exists(config_dir):
        for file in os.listdir(config_dir):
            if file.endswith('.yaml') or file.endswith('.yml'):
                display_name = file.replace('_', ' ').replace('.yaml', '').replace('.yml', '').title()
                config_files.append((file, display_name))
    
    selected_config = st.sidebar.selectbox(
        "Select configuration to view:",
        options=[None] + [f[0] for f in config_files],
        format_func=lambda x: "Choose a config..." if x is None else x
    )
    
    return selected_config


def display_config_content(selected_config: str):
    """Display configuration content in main panel."""
    if not selected_config:
        return
    
    st.header(f"📄 Configuration: {selected_config}")
    
    config_path = f"config/{selected_config}"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
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
        
        st.subheader("Configuration Content")
        st.text_area(
            "YAML Configuration:",
            value=config_content,
            height=600,
            key=f"config_viewer_main_{selected_config}",
            help="You can copy sections from this configuration for use in validation tools"
        )
        
        # Show statistics
        display_config_statistics(config_content)
        
    except FileNotFoundError:
        st.error(f"Configuration file {selected_config} not found")
    except Exception as e:
        st.error(f"Error reading configuration: {e}")


def display_config_statistics(config_content: str):
    """Display configuration statistics."""
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