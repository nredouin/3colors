"""
Hair Color Analysis Streamlit App
L'Oréal Hair Color Distribution Visualization with Color Remapping
"""
import streamlit as st
import pandas as pd
from src.data_loader import (
    load_respondent_data, get_available_shades, 
    load_respondent_image, load_respondent_mask,
    build_image_path, build_mask_path
)
from src.color_viz import create_color_bars
from src.color_processing import process_hair_color_remapping_with_sample, get_sample_info
from src.swatch_loader import (
    load_swatch_for_respondent_and_shade, extract_shade_id_from_data, 
    get_mapping_info, reload_mappings
)
from config.settings import logger, CITY_FOLDERS

# Page configuration
st.set_page_config(
    page_title="L'Oréal Hair Color Analysis",
    page_icon="💇‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2649B2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stSelectbox > div > div > div {
        background-color: #D4D9F0;
    }
    .image-container {
        border: 2px solid #2649B2;
        border-radius: 10px;
        padding: 10px;
        background-color: #f8f9fa;
    }
    .remapped-container {
        border: 2px solid #9D5CE6;
        border-radius: 10px;
        padding: 10px;
        background-color: #f8f4ff;
    }
    .swatch-container {
        border: 2px solid #4A74F3;
        border-radius: 10px;
        padding: 15px;
        background-color: #f0f4ff;
        margin-top: 1rem;
    }
    .sample-info {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">L\'Oréal Hair Color Analysis</h1>', unsafe_allow_html=True)

# Sidebar for controls
with st.sidebar:
    st.header("Controls")
    
    # Respondent ID input
    respondent_id = st.text_input(
        "Respondent ID (4 digits)",
        value="1001",
        max_chars=4,
        help="Enter a 4-digit respondent ID. First digit indicates the city."
    )
    
    # Validate respondent ID
    if respondent_id and len(respondent_id) == 4:
        try:
            city_code = int(respondent_id[0])
            if city_code in CITY_FOLDERS:
                city_name = CITY_FOLDERS[city_code].replace("mcb_hair_bucket_", "").title()
                st.success(f"City: {city_name}")
                
                # Get available shades
                available_shades = get_available_shades(respondent_id)
                
                if available_shades:
                    selected_shade = st.selectbox(
                        "Select Shade",
                        options=available_shades,
                        help="Choose a hair shade for analysis"
                    )
                else:
                    st.error("No shades found for this respondent ID")
                    selected_shade = None
            else:
                st.error("Invalid city code (must be 1-7)")
                selected_shade = None
        except ValueError:
            st.error("Invalid respondent ID format")
            selected_shade = None
    else:
        st.warning("Please enter a 4-digit respondent ID")
        selected_shade = None
    
    # Debug section for mapping
    st.divider()
    st.subheader("Debug Info")
    if st.button("Check Mapping Files"):
        mapping_info = get_mapping_info()
        
        # Shades mapping info
        shades_info = mapping_info['shades_mapping']
        if shades_info['file_exists']:
            st.success(f"✅ Shades mapping: {shades_info['total_entries']} entries")
            if shades_info['sample_entries']:
                st.write("Sample shades:")
                for entry in shades_info['sample_entries']:
                    st.write(f"• {entry['name'][:30]}...")
                    st.write(f"  L:{entry['light']} M:{entry['medium']} D:{entry['dark']}")
        else:
            st.error(f"❌ Shades mapping not found")
        
        # Hair category info
        category_info = mapping_info['hair_category']
        if category_info['file_exists']:
            st.success(f"✅ Hair category: {category_info['total_entries']} entries")
            if category_info['sample_entries']:
                st.write("Sample categories:")
                for entry in category_info['sample_entries']:
                    st.write(f"• {entry['respondent_id']} → {entry['category']}")
        else:
            st.error(f"❌ Hair category not found")
    
    if st.button("Reload Mappings"):
        shades_count, category_count = reload_mappings()
        st.success(f"Mappings reloaded! Shades: {shades_count}, Categories: {category_count}")

# Main content
if respondent_id and selected_shade:
    # Load data, image, and mask
    with st.spinner("Loading hair color data, image, and mask..."):
        df = load_respondent_data(respondent_id, selected_shade)
        image = load_respondent_image(respondent_id, selected_shade)
        mask = load_respondent_mask(respondent_id, selected_shade)
    
    if not df.empty:
        # Get sample information for selection
        samples_info = get_sample_info(df)
        
        # Display main metrics
        col_info1, col_info2, col_info3, col_info4 = st.columns(4)
        
        with col_info1:
            st.metric("Respondent ID", respondent_id)
        with col_info2:
            st.metric("Selected Shade", selected_shade)
        with col_info3:
            st.metric("Samples Found", len(df))
        with col_info4:
            city_name = CITY_FOLDERS[int(respondent_id[0])].replace("mcb_hair_bucket_", "").title()
            st.metric("City", city_name)
        
        st.divider()
        
        # Sample selection section
        st.subheader("🎨 Choose Sample for Color Remapping")
        
        # Create options for selectbox with detailed info
        sample_options = []
        for i, sample in enumerate(samples_info):
            proportions_str = f"{sample['proportions'][0]:.1f}% | {sample['proportions'][1]:.1f}% | {sample['proportions'][2]:.1f}%"
            option_text = f"Sample {i+1}: {proportions_str} (Score: {sample['balance_score']:.1f})"
            sample_options.append(option_text)
        
        col_select1, col_select2 = st.columns([2, 1])
        
        with col_select1:
            selected_sample_index = st.selectbox(
                "Select which sample to use for color remapping:",
                options=range(len(samples_info)),
                format_func=lambda x: sample_options[x],
                help="Choose the sample with color proportions you prefer for remapping"
            )
        
        with col_select2:
            if st.button("🔄 Use Best Balanced", help="Select the most balanced sample (closest to 33% each)"):
                # Find the sample with the lowest balance score
                best_sample = min(samples_info, key=lambda x: x['balance_score'])
                selected_sample_index = best_sample['index']
                st.rerun()
        
        # Show selected sample details
        if selected_sample_index is not None:
            selected_sample = samples_info[selected_sample_index]
            
            st.markdown('<div class="sample-info">', unsafe_allow_html=True)
            col_detail1, col_detail2, col_detail3 = st.columns(3)
            
            with col_detail1:
                st.write(f"**Selected:** Sample {selected_sample_index + 1}")
                st.write(f"**File:** {selected_sample['filename']}")
            
            with col_detail2:
                proportions = selected_sample['proportions']
                st.write(f"**Color 1:** {proportions[0]:.1f}%")
                st.write(f"**Color 2:** {proportions[1]:.1f}%")
                st.write(f"**Color 3:** {proportions[2]:.1f}%")
            
            with col_detail3:
                st.write(f"**Balance Score:** {selected_sample['balance_score']:.1f}")
                balance_quality = "Excellent" if selected_sample['balance_score'] < 10 else "Good" if selected_sample['balance_score'] < 20 else "Fair"
                st.write(f"**Quality:** {balance_quality}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Main content in 3 columns
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            st.subheader("Original Image")
            
            if image:
                st.markdown('<div class="image-container">', unsafe_allow_html=True)
                st.image(
                    image, 
                    caption=f"Original - {respondent_id} - {selected_shade}",
                    use_column_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Image info
                st.write(f"**Size:** {image.size[0]} x {image.size[1]} px")
                st.write(f"**Format:** {image.format}")
            else:
                st.error("Original image not found")
                expected_path = build_image_path(respondent_id, selected_shade)
                st.code(expected_path, language="text")
        
        with col2:
            st.subheader("Color Distribution")
            
            # Create and display the color bars
            fig = create_color_bars(df)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show sample files
            if 'filename' in df.columns:
                with st.expander("All Sample Files"):
                    for idx, filename in enumerate(df['filename']):
                        is_selected = idx == selected_sample_index
                        status = "🎯 SELECTED" if is_selected else ""
                        st.write(f"**Sample {idx+1}:** {filename} {status}")
        
        with col3:
            st.subheader("Remapped Colors")
            
            if image and mask and selected_sample_index is not None:
                with st.spinner(f"Processing color remapping with Sample {selected_sample_index + 1}..."):
                    try:
                        remapped_image = process_hair_color_remapping_with_sample(
                            image, mask, df, selected_sample_index
                        )
                        
                        st.markdown('<div class="remapped-container">', unsafe_allow_html=True)
                        st.image(
                            remapped_image,
                            caption=f"Remapped - Sample {selected_sample_index + 1} - {selected_shade}",
                            use_column_width=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.success(f"✨ Remapped with Sample {selected_sample_index + 1}!")
                        
                    except Exception as e:
                        st.error(f"Error in color remapping: {str(e)}")
                        
            elif not mask:
                st.error("Mask not found")
                expected_mask_path = build_mask_path(respondent_id, selected_shade)
                st.code(expected_mask_path, language="text")
            elif not image:
                st.warning("Original image required for remapping")
            else:
                st.info("Select a sample above to see remapped result")
        
        # Detailed data table and swatch (full width)
        with st.expander("View Detailed Color Data"):
            # Highlight selected sample in dataframe
            styled_df = df.copy()
            if selected_sample_index is not None:
                # Add a column to show which sample is selected
                styled_df['Selected'] = ['🎯 YES' if i == selected_sample_index else '' for i in range(len(styled_df))]
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Load and display swatch
            st.subheader("Color Swatch Reference")
            
            with st.spinner("Loading color swatch..."):
                # Extract shade ID from data
                shade_id = extract_shade_id_from_data(df)
                
                if shade_id:
                    st.info(f"Looking for swatch - Respondent: **{respondent_id}**, Shade ID: **{shade_id}**")
                    
                    # Use the new two-step mapping process
                    swatch_image, swatch_info = load_swatch_for_respondent_and_shade(respondent_id, shade_id)
                    
                    if swatch_image and swatch_info:
                        col_swatch1, col_swatch2 = st.columns([1, 2])
                        
                        with col_swatch1:
                            st.markdown('<div class="swatch-container">', unsafe_allow_html=True)
                            st.image(
                                swatch_image,
                                caption=f"Swatch: {swatch_info['name']}",
                                width=200
                            )
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_swatch2:
                            st.write("**Swatch Information:**")
                            st.write(f"**Name:** {swatch_info['name']}")
                            st.write(f"**Category:** {swatch_info['mapping_category'].title()}")
                            st.write(f"**Filename:** {swatch_info['filename']}")
                            st.write(f"**Folder:** {swatch_info['folder']}")
                            st.write(f"**Path:** `{swatch_info['path']}`")
                            
                    else:
                        st.warning(f"No swatch found for Respondent {respondent_id}, Shade ID: {shade_id}")
                        st.info("Check the mapping files in Debug Info section")
                else:
                    st.warning("Could not extract shade ID from data for swatch lookup")
                    st.info("Available columns in data:")
                    st.write(df.columns.tolist())
            
    else:
        st.error(f"No data found for Respondent {respondent_id} with shade '{selected_shade}'")

else:
    # Welcome message
    st.info("👆 Please select a Respondent ID and Shade from the sidebar to begin analysis.")
    
    # Show city mapping
    st.subheader("City Codes")
    city_df = pd.DataFrame([
        {"Code": k, "City": v.replace("mcb_hair_bucket_", "").title()} 
        for k, v in CITY_FOLDERS.items()
    ])
    st.table(city_df)