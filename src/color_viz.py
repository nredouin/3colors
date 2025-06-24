"""Color visualization utilities"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import luxpy as lx
from config.settings import logger

def lab_to_rgb(lab_values):
    """Convert Lab values to RGB values (0-255 range) using luxpy."""
    lab_array = np.array(lab_values).reshape(1, 3)
    
    # Convert Lab to XYZ
    xyz_array = lx.lab_to_xyz(lab_array)
    
    # Convert XYZ to sRGB - this already returns values in 0-255 range
    rgb_array = lx.xyz_to_srgb(xyz_array)
    
    # Clip values to valid range and convert to integers
    rgb_255 = np.clip(rgb_array.flatten(), 0, 255).astype(np.uint8)
    
    return rgb_255

def create_color_bars(df: pd.DataFrame) -> go.Figure:
    """
    Create horizontal bar chart showing color distribution
    
    Args:
        df (pd.DataFrame): DataFrame with color data
        
    Returns:
        go.Figure: Plotly figure
    """
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            font=dict(size=16)
        )
        return fig
    
    fig = go.Figure()
    
    # L'Oréal color palette as fallback
    loreal_colors = ['#2649B2', '#4A74F3', '#8E7DE3', '#9D5CE6', '#D4D9F0', '#6C8BE0', '#B55CE6']
    
    for idx, row in df.iterrows():
        # Extract the 3 colors and their proportions
        colors_data = []
        for i in range(1, 4):  # 3 clusters
            L = row[f'L_{i}']
            a = row[f'a_{i}']
            b = row[f'b_{i}']
            proportion = row[f'proportion_{i}']
            
            # Convert LAB to RGB using luxpy for accurate colors
            try:
                lab_values = [L, a, b]
                rgb_values = lab_to_rgb(lab_values)
                rgb_color = f'rgb({rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]})'
            except Exception as e:
                logger.warning(f"Error converting LAB to RGB for sample {idx}, cluster {i}: {e}")
                # Fallback to L'Oréal palette color
                rgb_color = loreal_colors[i-1] if i-1 < len(loreal_colors) else '#CCCCCC'
            
            colors_data.append({
                'color': rgb_color,
                'proportion': proportion,
                'lab': f'L:{L:.1f} a:{a:.1f} b:{b:.1f}'
            })
        
        # Create stacked bar for this row
        y_pos = f"Sample {idx + 1}"
        x_start = 0
        
        for i, color_info in enumerate(colors_data):
            fig.add_trace(go.Bar(
                name=f'Color {i+1}' if idx == 0 else None,  # Only show legend for first row
                x=[color_info['proportion']],
                y=[y_pos],
                orientation='h',
                marker_color=color_info['color'],
                text=f"{color_info['proportion']:.1f}%",
                textposition='inside',
                hovertemplate=f"<b>Color {i+1}</b><br>" +
                             f"Proportion: {color_info['proportion']:.1f}%<br>" +
                             f"LAB: {color_info['lab']}<br>" +
                             "<extra></extra>",
                showlegend=(idx == 0),  # Only show legend for first row
                offsetgroup=idx,
                base=x_start
            ))
            x_start += color_info['proportion']
    
    fig.update_layout(
        title="Hair Color Distribution",
        xaxis_title="Proportion (%)",
        yaxis_title="Samples",
        barmode='stack',
        height=800,
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.1,  # Thick bars as requested
        bargroupgap=0.05,
        margin=dict(l=80, r=80, t=80, b=80)
    )
    
    # Add grid
    fig.update_xaxes(gridcolor='lightgray')
    fig.update_yaxes(gridcolor='lightgray')
    
    return fig