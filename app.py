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
    get_mapping_info, reload_mappings, get_respondent_info
)
from src.quantile_analysis import select_representative_samples_quantile
from src.quantile_viz import create_grid_visualization_with_images
from config.settings import logger, CITY_FOLDERS

# Page configuration
st.set_page_config(
    page_title="L'Oréal Hair Color Analysis",
    page_icon="💇‍♀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for tab tracking
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

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
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #D4D9F0;
        border-radius: 4px 4px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2649B2;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<h1 class="main-header">L\'Oréal Hair Color Analysis</h1>', unsafe_allow_html=True)

# Create tabs with callback to track active tab
tab1, tab2 = st.tabs(["🎨 Color Remapping", "📊 Quantile Grid Analysis"])

# Detect which tab is being viewed using a hidden radio button trick
tab_selection = st.radio(
    "Select Tab",
    options=["Color Remapping", "Quantile Grid Analysis"],
    index=st.session_state.active_tab,
    key="tab_selector",
    label_visibility="collapsed"
)

# Update session state based on tab selection
if tab_selection == "Color Remapping":
    st.session_state.active_tab = 0
else:
    st.session_state.active_tab = 1

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: Original Color Remapping Feature
# ═══════════════════════════════════════════════════════════════════════════════

with tab1:
    if st.session_state.active_tab == 0:  # Only execute if this tab is active
        # Sidebar for controls
        with st.sidebar:
            st.header("Controls - Color Remapping")
            
            # Respondent ID input
            respondent_id = st.text_input(
                "Respondent ID (4 digits)",
                value="1001",
                max_chars=4,
                help="Enter a 4-digit respondent ID. First digit indicates the city.",
                key="remap_resp_id"
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
                                help="Choose a hair shade for analysis",
                                key="remap_shade"
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
            if st.button("Check Mapping Files", key="check_mapping"):
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
            
            if st.button("Reload Mappings", key="reload_mapping"):
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
                
                respondent_info = get_respondent_info(respondent_id)
                # Display main metrics
                col_info1, col_info2, col_info3, col_info4, col_info5, col_info6 = st.columns(6)
                
                with col_info1:
                    st.metric("Respondent ID", respondent_id)
                with col_info2:
                    st.metric("Selected Shade", selected_shade)
                with col_info3:
                    st.metric("Samples Found", len(df))
                with col_info4:
                    city_name = CITY_FOLDERS[int(respondent_id[0])].replace("mcb_hair_bucket_", "").title()
                    st.metric("City", city_name)
                with col_info5:
                    hair_tone = respondent_info['hair_tone'] if respondent_info['hair_tone'] else "Unknown"
                    st.metric("Hair Tone", hair_tone)
                with col_info6:
                    skin_tone = respondent_info['skin_tone_cluster'] if respondent_info['skin_tone_cluster'] else "Unknown"
                    st.metric("Skin Tone Cluster", skin_tone)
                
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
                        help="Choose the sample with color proportions you prefer for remapping",
                        key="sample_select"
                    )
                
                with col_select2:
                    if st.button("🔄 Use Best Balanced", help="Select the most balanced sample (closest to 33% each)", key="best_balanced"):
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
                col1, col2, col3 = st.columns([1, 1.5, 1])
                
                with col1:
                    st.subheader("Original Image")
                    
                    if image:
                        st.markdown('<div class="image-container">', unsafe_allow_html=True)
                        st.image(
                            image, 
                            caption=f"Original - {respondent_id} - {selected_shade}",
                            use_container_width=True
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
                                    use_container_width=True
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
    else:
        st.info("👈 Switch to this tab to use Color Remapping features")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: Quantile Grid Analysis
# ═══════════════════════════════════════════════════════════════════════════════

with tab2:
    if st.session_state.active_tab == 1:  # Only execute if this tab is active
        st.header("📊 Quantile-Based Grid Analysis")
        st.markdown("""
        This analysis uses quantile-based binning to select representative hair samples across 
        the L-C (Lightness-Chroma) and L-h (Lightness-Hue) color spaces.
        """)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload CSV file for analysis",
            type=['csv'],
            help="Upload a CSV file containing hair color data with RESP_FINAL, VIDEOS, L_main, a_main, b_main, L_reflect, a_reflect, b_reflect columns",
            key="quantile_csv_upload"
        )
        
        if uploaded_file is not None:
            try:
                # Try different separators
                try:
                    df_analysis = pd.read_csv(uploaded_file, sep=';')
                except:
                    uploaded_file.seek(0)
                    df_analysis = pd.read_csv(uploaded_file, sep=',')
                
                st.success(f"✅ CSV loaded successfully! Total rows: {len(df_analysis)}")
                
                # Display file info
                col_file1, col_file2, col_file3 = st.columns(3)
                with col_file1:
                    st.metric("Total Samples", len(df_analysis))
                with col_file2:
                    if 'color_regions' in df_analysis.columns:
                        st.metric("Regions", df_analysis['color_regions'].nunique())
                    else:
                        st.metric("Regions", "N/A")
                with col_file3:
                    st.metric("Columns", len(df_analysis.columns))
                
                # Show available columns
                with st.expander("View Available Columns"):
                    st.write(df_analysis.columns.tolist())
                    st.dataframe(df_analysis.head(3))
                
                # Check for required columns
                required_cols = ['RESP_FINAL', 'VIDEOS', 'L_main', 'a_main', 'b_main', 'L_reflect', 'a_reflect', 'b_reflect']
                missing_cols = [col for col in required_cols if col not in df_analysis.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                    st.info("Required columns: " + ", ".join(required_cols))
                else:
                    # Region selection
                    if 'color_regions' in df_analysis.columns:
                        available_regions = sorted(df_analysis['color_regions'].unique())
                        
                        col_region1, col_region2 = st.columns([2, 1])
                        
                        with col_region1:
                            selected_region = st.selectbox(
                                "Select Region to Analyze",
                                options=available_regions,
                                help="Choose which color region to analyze",
                                key="quantile_region"
                            )
                        
                        with col_region2:
                            grid_size = st.slider(
                                "Grid Size",
                                min_value=2,
                                max_value=6,
                                value=4,
                                help="Number of bins per dimension (e.g., 4 = 4x4 grid)",
                                key="grid_size"
                            )
                        
                        # Filter data for selected region
                        df_region = df_analysis[df_analysis['color_regions'] == selected_region].copy()
                        
                        if len(df_region) > 0:
                            st.info(f"📍 Region {selected_region}: **{len(df_region)}** samples found")
                            
                            # Analysis tabs for main and reflect
                            analysis_tab1, analysis_tab2 = st.tabs(["🎨 Main Color", "✨ Reflect Color"])
                            
                            # MAIN COLOR ANALYSIS
                            with analysis_tab1:
                                st.subheader(f"Main Color Analysis - Region {selected_region}")
                                
                                with st.spinner("Running quantile-based sampling for main color..."):
                                    try:
                                        selected_data_main = select_representative_samples_quantile(
                                            df_region,
                                            selected_region,
                                            color_type='main',
                                            grid_size=grid_size
                                        )
                                        
                                        # Display metrics
                                        col_m1, col_m2, col_m3 = st.columns(3)
                                        with col_m1:
                                            st.metric("L-C Grid Samples", len(selected_data_main['lc_samples']))
                                        with col_m2:
                                            st.metric("L-h Grid Samples", len(selected_data_main['lh_samples']))
                                        with col_m3:
                                            st.metric("Grid Size", f"{grid_size}x{grid_size}")
                                        
                                        # Create and display visualization
                                        fig_main = create_grid_visualization_with_images(
                                            selected_data_main,
                                            selected_region,
                                            color_type='main',
                                            image_size=(80, 80)
                                        )
                                        
                                        st.plotly_chart(fig_main, use_container_width=True)
                                        
                                        # ===== IMAGE GALLERIES =====
                                        st.markdown("---")
                                        st.subheader("📸 Image Galleries - Clearer View")

                                        gallery_col1, gallery_col2 = st.columns(2)

                                        # L-C Gallery
                                        with gallery_col1:
                                            st.markdown("##### L vs C Grid Images")
                                            from src.quantile_viz import load_images_for_gallery
                                            
                                            images_lc = load_images_for_gallery(selected_data_main['lc_samples'])
                                            
                                            if images_lc:
                                                # Create proper grid with correct positions
                                                for row_idx in range(grid_size):
                                                    cols = st.columns(grid_size)
                                                    for col_idx in range(grid_size):
                                                        # Find image that belongs in this grid position
                                                        matching_img = None
                                                        for img_info in images_lc:
                                                            if 'L_bin' in img_info and 'C_bin' in img_info:
                                                                if img_info['L_bin'] == row_idx and img_info['C_bin'] == col_idx:
                                                                    matching_img = img_info
                                                                    break
                                                        
                                                        with cols[col_idx]:
                                                            if matching_img:
                                                                st.image(
                                                                    matching_img['image'],
                                                                    caption=f"{matching_img['respondent_id']} - {matching_img['shade']}\nL:{matching_img['L']:.1f} C:{matching_img['C']:.1f}",
                                                                    use_container_width=True
                                                                )
                                                            else:
                                                                # Empty cell - show placeholder
                                                                st.write("")
                                            else:
                                                st.warning("No images loaded for L-C grid")

                                        # L-h Gallery
                                        with gallery_col2:
                                            st.markdown("##### L vs h Grid Images")
                                            
                                            images_lh = load_images_for_gallery(selected_data_main['lh_samples'])
                                            
                                            if images_lh:
                                                # Create proper grid with correct positions
                                                for row_idx in range(grid_size):
                                                    cols = st.columns(grid_size)
                                                    for col_idx in range(grid_size):
                                                        # Find image that belongs in this grid position
                                                        matching_img = None
                                                        for img_info in images_lh:
                                                            if 'L_bin_h' in img_info and 'h_bin' in img_info:
                                                                if img_info['L_bin_h'] == row_idx and img_info['h_bin'] == col_idx:
                                                                    matching_img = img_info
                                                                    break
                                                        
                                                        with cols[col_idx]:
                                                            if matching_img:
                                                                st.image(
                                                                    matching_img['image'],
                                                                    caption=f"{matching_img['respondent_id']} - {matching_img['shade']}\nL:{matching_img['L']:.1f} h:{matching_img['h']:.1f}°",
                                                                    use_container_width=True
                                                                )
                                                            else:
                                                                # Empty cell - show placeholder
                                                                st.write("")
                                            else:
                                                st.warning("No images loaded for L-h grid")
                                        
                                        # Export options
                                        st.markdown("---")
                                        st.subheader("📥 Export Data")
                                        col_exp1, col_exp2 = st.columns(2)
                                        
                                        with col_exp1:
                                            csv_lc_main = selected_data_main['lc_samples'][['RESP_FINAL', 'VIDEOS', 'XSHADE_S', 'L', 'C', 'h', 'L_bin', 'C_bin']].to_csv(index=False)
                                            st.download_button(
                                                label="📥 Download L-C Grid Data (Main)",
                                                data=csv_lc_main,
                                                file_name=f"region_{selected_region}_main_LC_grid.csv",
                                                mime="text/csv",
                                                key="download_lc_main"
                                            )
                                        
                                        with col_exp2:
                                            csv_lh_main = selected_data_main['lh_samples'][['RESP_FINAL', 'VIDEOS', 'XSHADE_S', 'L', 'C', 'h', 'L_bin_h', 'h_bin']].to_csv(index=False)
                                            st.download_button(
                                                label="📥 Download L-h Grid Data (Main)",
                                                data=csv_lh_main,
                                                file_name=f"region_{selected_region}_main_Lh_grid.csv",
                                                mime="text/csv",
                                                key="download_lh_main"
                                            )
                                        
                                    except Exception as e:
                                        st.error(f"Error in main color analysis: {str(e)}")
                                        logger.error(f"Main color analysis error: {e}")
                            
                            # REFLECT COLOR ANALYSIS
                            with analysis_tab2:
                                st.subheader(f"Reflect Color Analysis - Region {selected_region}")
                                
                                with st.spinner("Running quantile-based sampling for reflect color..."):
                                    try:
                                        selected_data_reflect = select_representative_samples_quantile(
                                            df_region,
                                            selected_region,
                                            color_type='reflect',
                                            grid_size=grid_size
                                        )
                                        
                                        # Display metrics
                                        col_r1, col_r2, col_r3 = st.columns(3)
                                        with col_r1:
                                            st.metric("L-C Grid Samples", len(selected_data_reflect['lc_samples']))
                                        with col_r2:
                                            st.metric("L-h Grid Samples", len(selected_data_reflect['lh_samples']))
                                        with col_r3:
                                            st.metric("Grid Size", f"{grid_size}x{grid_size}")
                                        
                                        # Create and display visualization
                                        fig_reflect = create_grid_visualization_with_images(
                                            selected_data_reflect,
                                            selected_region,
                                            color_type='reflect',
                                            image_size=(80, 80)
                                        )
                                        
                                        st.plotly_chart(fig_reflect, use_container_width=True)
                                        
                                        # ===== IMAGE GALLERIES =====# ===== IMAGE GALLERIES =====
                                        st.markdown("---")
                                        st.subheader("📸 Image Galleries - Clearer View")

                                        gallery_col1, gallery_col2 = st.columns(2)

                                        # L-C Gallery
                                        with gallery_col1:
                                            st.markdown("##### L vs C Grid Images")
                                            from src.quantile_viz import load_images_for_gallery
                                            
                                            images_lc = load_images_for_gallery(selected_data_main['lc_samples'])
                                            
                                            if images_lc:
                                                # Create proper grid with correct positions
                                                for row_idx in range(grid_size):
                                                    cols = st.columns(grid_size)
                                                    for col_idx in range(grid_size):
                                                        # Find image that belongs in this grid position
                                                        matching_img = None
                                                        for img_info in images_lc:
                                                            if 'L_bin' in img_info and 'C_bin' in img_info:
                                                                if img_info['L_bin'] == row_idx and img_info['C_bin'] == col_idx:
                                                                    matching_img = img_info
                                                                    break
                                                        
                                                        with cols[col_idx]:
                                                            if matching_img:
                                                                st.image(
                                                                    matching_img['image'],
                                                                    caption=f"{matching_img['respondent_id']} - {matching_img['shade']}\nL:{matching_img['L']:.1f} C:{matching_img['C']:.1f}",
                                                                    use_container_width=True
                                                                )
                                                            else:
                                                                # Empty cell - show placeholder
                                                                st.write("")
                                            else:
                                                st.warning("No images loaded for L-C grid")

                                        # L-h Gallery
                                        with gallery_col2:
                                            st.markdown("##### L vs h Grid Images")
                                            
                                            images_lh = load_images_for_gallery(selected_data_main['lh_samples'])
                                            
                                            if images_lh:
                                                # Create proper grid with correct positions
                                                for row_idx in range(grid_size):
                                                    cols = st.columns(grid_size)
                                                    for col_idx in range(grid_size):
                                                        # Find image that belongs in this grid position
                                                        matching_img = None
                                                        for img_info in images_lh:
                                                            if 'L_bin_h' in img_info and 'h_bin' in img_info:
                                                                if img_info['L_bin_h'] == row_idx and img_info['h_bin'] == col_idx:
                                                                    matching_img = img_info
                                                                    break
                                                        
                                                        with cols[col_idx]:
                                                            if matching_img:
                                                                st.image(
                                                                    matching_img['image'],
                                                                    caption=f"{matching_img['respondent_id']} - {matching_img['shade']}\nL:{matching_img['L']:.1f} h:{matching_img['h']:.1f}°",
                                                                    use_container_width=True
                                                                )
                                                            else:
                                                                # Empty cell - show placeholder
                                                                st.write("")
                                            else:
                                                st.warning("No images loaded for L-h grid")
                                        
                                        # Export options
                                        st.markdown("---")
                                        st.subheader("📥 Export Data")
                                        col_expr1, col_expr2 = st.columns(2)
                                        
                                        with col_expr1:
                                            csv_lc_reflect = selected_data_reflect['lc_samples'][['RESP_FINAL', 'VIDEOS', 'XSHADE_S', 'L', 'C', 'h', 'L_bin', 'C_bin']].to_csv(index=False)
                                            st.download_button(
                                                label="📥 Download L-C Grid Data (Reflect)",
                                                data=csv_lc_reflect,
                                                file_name=f"region_{selected_region}_reflect_LC_grid.csv",
                                                mime="text/csv",
                                                key="download_lc_reflect"
                                            )
                                        
                                        with col_expr2:
                                            csv_lh_reflect = selected_data_reflect['lh_samples'][['RESP_FINAL', 'VIDEOS', 'XSHADE_S', 'L', 'C', 'h', 'L_bin_h', 'h_bin']].to_csv(index=False)
                                            st.download_button(
                                                label="📥 Download L-h Grid Data (Reflect)",
                                                data=csv_lh_reflect,
                                                file_name=f"region_{selected_region}_reflect_Lh_grid.csv",
                                                mime="text/csv",
                                                key="download_lh_reflect"
                                            )
                                        
                                    except Exception as e:
                                        st.error(f"Error in reflect color analysis: {str(e)}")
                                        logger.error(f"Reflect color analysis error: {e}")
                            
                        else:
                            st.error(f"No samples found for region {selected_region}")
                    
                    else:
                        st.error("❌ Column 'color_regions' not found in CSV")
                        st.info("Please ensure your CSV has a 'color_regions' column")
            
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
                logger.error(f"CSV loading error: {e}")
        
        else:
            st.info("👆 Please upload a CSV file to begin quantile grid analysis")
            
            st.markdown("""
            ### Expected CSV Format
            
            Your CSV should contain the following columns:
            - `RESP_FINAL`: Respondent ID (should match your 4-digit format)
            - `VIDEOS`: Video/Shade identifier
            - `color_regions`: Region number for grouping samples
            - `L_main`, `a_main`, `b_main`: Lab color values for main color
            - `L_reflect`, `a_reflect`, `b_reflect`: Lab color values for reflect color
            - `XSHADE_S` (optional): Shade name
            
            The analysis will load actual respondent images based on the RESP_FINAL and VIDEOS values.
            """)
    else:
        st.info("👈 Switch to this tab to use Quantile Grid Analysis")