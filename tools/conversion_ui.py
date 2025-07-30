"""
Conversion UI module for JSON Reports Tools
Handles the UI for JSON conversion between NameValuePair and ObjectHierarchy formats
"""

import streamlit as st
import json
import logging
from tools.json_converter import ConversionManager
from tools.ui_helpers import load_json_data, create_json_editor, create_download_section, create_process_control_buttons

logger = logging.getLogger(__name__)


def render_conversion_ui(tool: str):
    """Render the conversion UI for the specified tool.
    
    Args:
        tool: The conversion tool ("Convert to NameValuePair" or "Convert to ObjectHierarchy")
    """
    st.header(f"{tool}")
    st.write("Upload a JSON file or paste the content:")
    
    # Load JSON data
    json_data = load_json_data()
    
    # JSON preview and editing section
    if json_data is not None:
        json_data = create_json_editor(json_data)
        st.session_state['json_data'] = json_data
    
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
    
    # Show previous results
    show_previous_results()


def handle_conversion(json_data: dict, tool: str, show_stats: bool, show_sample: bool, show_preview: bool):
    """Handle the conversion process.
    
    Args:
        json_data: JSON data to convert
        tool: Conversion tool name
        show_stats: Whether to show statistics
        show_sample: Whether to show structure sample
        show_preview: Whether to show result preview
    """
    if json_data is None:
        st.error("No JSON data available for conversion")
        logger.error("No JSON data available for conversion")
        return
    
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
        from app import clean_bytes_from_result
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
        logger.error(f"Exception during conversion: {e}")
        st.error(f"Conversion error: {e}")


def display_conversion_results(result: dict, show_preview: bool, show_stats: bool, show_sample: bool):
    """Display conversion results.
    
    Args:
        result: Conversion result
        show_preview: Whether to show preview
        show_stats: Whether to show statistics
        show_sample: Whether to show sample
    """
    st.subheader("✅ Conversion Results")
    st.success("Conversion completed successfully!")
    
    # Download section
    create_download_section(result, "result.json")
    
    # Show preview of result (only if enabled)
    if show_preview:
        st.markdown("### 👀 Result Preview")
        st.info("Here's a preview of your converted data:")
        st.json(result)
    
    # Show statistics
    if show_stats and st.session_state.get('conversion_stats'):
        display_conversion_statistics(st.session_state['conversion_stats'])
    
    # Show sample
    if show_sample and st.session_state.get('conversion_sample'):
        display_conversion_sample(st.session_state['conversion_sample'])
    
    # Process control buttons
    create_process_control_buttons()


def display_conversion_statistics(stats: dict):
    """Display conversion statistics.
    
    Args:
        stats: Statistics dictionary
    """
    st.subheader("📊 Conversion Statistics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Keys", stats['total_keys'])
    with col2:
        st.metric("Processed Keys", stats['processed_keys'])
    with col3:
        st.metric("Errors", stats['errors'])
    
    st.info(f"Conversion type: {stats['conversion_type']}")


def display_conversion_sample(sample_text: str):
    """Display conversion sample.
    
    Args:
        sample_text: Sample text to display
    """
    st.subheader("📋 Structure Sample")
    st.code(sample_text, language="json")


def show_previous_results():
    """Show previous conversion results if available."""
    if st.session_state.get('conversion_completed', False):
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
                display_conversion_statistics(st.session_state['conversion_stats'])
            
            # Show sample if enabled
            if show_sample and st.session_state.get('conversion_sample'):
                display_conversion_sample(st.session_state['conversion_sample'])
            
            # Process control buttons
            st.markdown("---")
            st.markdown("### 🔄 Process Control")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📁 Start New Conversion", type="primary", key="new_conv_prev"):
                    from tools.ui_helpers import clear_all_session_state
                    clear_all_session_state()
                    st.rerun()
            with col2:
                if st.button("🏠 Back to Welcome", type="secondary", key="back_welcome_prev"):
                    st.session_state['selected_tool'] = "Welcome"
                    from tools.ui_helpers import clear_all_session_state
                    clear_all_session_state()
                    st.rerun() 