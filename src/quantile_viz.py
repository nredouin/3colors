"""Visualization for quantile-based grid analysis with images"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from config.settings import logger
from src.data_loader import load_respondent_image
from src.quantile_analysis import format_respondent_id, format_shade_name
import base64
from io import BytesIO

def pil_to_base64(image, size=(100, 100)):
    """Convert PIL Image to base64 string for Plotly"""
    if image is None:
        return None
    
    try:
        # Resize image
        img_resized = image.resize(size)
        
        # Convert to base64
        buffered = BytesIO()
        img_resized.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None

def create_grid_visualization_with_images(selected_data, region_num, color_type='main', 
                                          image_size=(80, 80)):
    """
    Create L-C and L-h grid visualizations with actual respondent images
    
    Parameters:
    - selected_data: Dictionary from select_representative_samples_quantile
    - region_num: Region number
    - color_type: 'main' or 'reflect'
    - image_size: Tuple for image dimensions
    
    Returns:
    - Plotly figure object
    """
    
    df_lc = selected_data['lc_samples']
    df_lh = selected_data['lh_samples']
    bins = selected_data['bins']
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f'L vs C Grid - {len(df_lc)} samples',
            f'L vs h Grid - {len(df_lh)} samples'
        ),
        horizontal_spacing=0.12
    )
    
    # ===== PLOT 1: L vs C =====
    for _, row in df_lc.iterrows():
        respondent_id = format_respondent_id(row['RESP_FINAL'])
        shade = format_shade_name(row['VIDEOS'])
        
        if respondent_id and shade:
            # Load image
            image = load_respondent_image(respondent_id, shade)
            
            if image:
                # Convert to base64
                img_base64 = pil_to_base64(image, image_size)
                
                if img_base64:
                    # Add image as layout image
                    fig.add_layout_image(
                        dict(
                            source=img_base64,
                            xref="x", yref="y",
                            x=row['C'], y=row['L'],
                            sizex=max(bins['C']) * 0.08,  # Adjust size based on data range
                            sizey=max(bins['L']) * 0.08,
                            xanchor="center", yanchor="middle",
                            layer="above"
                        )
                    )
                    
                    # Add invisible scatter point for hover info
                    fig.add_trace(
                        go.Scatter(
                            x=[row['C']],
                            y=[row['L']],
                            mode='markers',
                            marker=dict(size=1, opacity=0),
                            hovertemplate=(
                                f"<b>Respondent:</b> {respondent_id}<br>"
                                f"<b>Shade:</b> {shade}<br>"
                                f"<b>L:</b> {row['L']:.2f}<br>"
                                f"<b>C:</b> {row['C']:.2f}<br>"
                                f"<b>h:</b> {row['h']:.2f}°<br>"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                            name=f"{respondent_id}_{shade}"
                        ),
                        row=1, col=1
                    )
    
    # Add grid lines for L-C
    for L_line in bins['L']:
        fig.add_hline(y=L_line, line_dash="dash", line_color="gray", 
                     opacity=0.3, row=1, col=1)
    for C_line in bins['C']:
        fig.add_vline(x=C_line, line_dash="dash", line_color="gray", 
                     opacity=0.3, row=1, col=1)
    
    # ===== PLOT 2: L vs h =====
    for _, row in df_lh.iterrows():
        respondent_id = format_respondent_id(row['RESP_FINAL'])
        shade = format_shade_name(row['VIDEOS'])
        
        if respondent_id and shade:
            # Load image
            image = load_respondent_image(respondent_id, shade)
            
            if image:
                # Convert to base64
                img_base64 = pil_to_base64(image, image_size)
                
                if img_base64:
                    # Add image as layout image
                    fig.add_layout_image(
                        dict(
                            source=img_base64,
                            xref="x2", yref="y2",
                            x=row['h'], y=row['L'],
                            sizex=360 * 0.08,  # Hue is 0-360
                            sizey=max(bins['L']) * 0.08,
                            xanchor="center", yanchor="middle",
                            layer="above"
                        )
                    )
                    
                    # Add invisible scatter point for hover info
                    fig.add_trace(
                        go.Scatter(
                            x=[row['h']],
                            y=[row['L']],
                            mode='markers',
                            marker=dict(size=1, opacity=0),
                            hovertemplate=(
                                f"<b>Respondent:</b> {respondent_id}<br>"
                                f"<b>Shade:</b> {shade}<br>"
                                f"<b>L:</b> {row['L']:.2f}<br>"
                                f"<b>C:</b> {row['C']:.2f}<br>"
                                f"<b>h:</b> {row['h']:.2f}°<br>"
                                "<extra></extra>"
                            ),
                            showlegend=False,
                            name=f"{respondent_id}_{shade}"
                        ),
                        row=1, col=2
                    )
    
    # Add grid lines for L-h
    for L_line in bins['L']:
        fig.add_hline(y=L_line, line_dash="dash", line_color="gray", 
                     opacity=0.3, row=1, col=2)
    for h_line in bins['h']:
        fig.add_vline(x=h_line, line_dash="dash", line_color="gray", 
                     opacity=0.3, row=1, col=2)
    
    # Update axes
    fig.update_xaxes(title_text="Chroma (C)", row=1, col=1)
    fig.update_yaxes(title_text="Lightness (L*)", row=1, col=1)
    
    fig.update_xaxes(title_text="Hue angle (h°)", row=1, col=2)
    fig.update_yaxes(title_text="Lightness (L*)", row=1, col=2)
    
    # Update layout
    fig.update_layout(
        title_text=f"Region {region_num} - Quantile-Based Grid Analysis ({color_type} color)",
        title_font_size=18,
        showlegend=False,
        height=600,
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Add grid styling
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
    
    return fig


def load_images_for_gallery(df_samples):
    """
    Load all images for gallery display
    
    Parameters:
    - df_samples: DataFrame with RESP_FINAL, VIDEOS, and bin columns
    
    Returns:
    - List of dictionaries with image info including bin positions
    """
    images_info = []
    
    for idx, row in df_samples.iterrows():
        respondent_id = format_respondent_id(row['RESP_FINAL'])
        shade = format_shade_name(row['VIDEOS'])
        
        if respondent_id and shade:
            image = load_respondent_image(respondent_id, shade)
            
            if image:
                img_data = {
                    'image': image,
                    'respondent_id': respondent_id,
                    'shade': shade,
                    'L': row['L'],
                    'C': row['C'],
                    'h': row['h']
                }
                
                # Add bin information if available
                if 'L_bin' in row:
                    img_data['L_bin'] = int(row['L_bin'])
                if 'C_bin' in row:
                    img_data['C_bin'] = int(row['C_bin'])
                if 'L_bin_h' in row:
                    img_data['L_bin_h'] = int(row['L_bin_h'])
                if 'h_bin' in row:
                    img_data['h_bin'] = int(row['h_bin'])
                
                images_info.append(img_data)
            else:
                logger.warning(f"Could not load image for {respondent_id} - {shade}")
    
    return images_info