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
from src.color_processing import process_hair_color_remapping
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

# Main content
if respondent_id and selected_shade:
    # Load data, image, and mask
    with st.spinner("Loading hair color data, image, and mask..."):
        df = load_respondent_data(respondent_id, selected_shade)
        image = load_respondent_image(respondent_id, selected_shade)
        mask = load_respondent_mask(respondent_id, selected_shade)
    
    if not df.empty:
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
                with st.expander("Sample Files"):
                    for idx, filename in enumerate(df['filename'].head(5)):
                        st.write(f"**Sample {idx+1}:** {filename}")
        
        with col3:
            st.subheader("Remapped Colors")
            
            if image and mask:
                with st.spinner("Processing color remapping..."):
                    try:
                        remapped_image = process_hair_color_remapping(image, mask, df)
                        
                        st.markdown('<div class="remapped-container">', unsafe_allow_html=True)
                        st.image(
                            remapped_image,
                            caption=f"Remapped - 3 Colors - {selected_shade}",
                            use_column_width=True
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        st.success("✨ Color remapping completed!")
                        
                    except Exception as e:
                        st.error(f"Error in color remapping: {str(e)}")
                        
            elif not mask:
                st.error("Mask not found")
                expected_mask_path = build_mask_path(respondent_id, selected_shade)
                st.code(expected_mask_path, language="text")
            else:
                st.warning("Original image required for remapping")
        
        # Detailed data table (full width)
        with st.expander("View Detailed Color Data"):
            st.dataframe(df, use_container_width=True)
            
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