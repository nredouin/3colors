"""Color visualization utilities"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from config.settings import logger

def lab_to_rgb(L, a, b):
    """
    Convert LAB color to RGB (simplified conversion)
    
    Args:
        L, a, b: LAB color values
        
    Returns:
        tuple: RGB values (0-255)
    """
    # Simplified LAB to RGB conversion
    # This is a basic approximation - you might want to use a proper color library
    
    # Normalize L (0-100 to 0-1)
    L_norm = L / 100.0
    
    # Simple conversion (not accurate, but for visualization)
    r = max(0, min(255, int(255 * (L_norm + a/100))))
    g = max(0, min(255, int(255 * (L_norm - a/200 + b/200))))
    b_val = max(0, min(255, int(255 * (L_norm - b/100))))
    
    return (r, g, b_val)

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
    
    # L'Oréal color palette
    loreal_colors = ['#2649B2', '#4A74F3', '#8E7DE3', '#9D5CE6', '#D4D9F0', '#6C8BE0', '#B55CE6']
    
    for idx, row in df.iterrows():
        # Extract the 3 colors and their proportions
        colors_data = []
        for i in range(1, 4):  # 3 clusters
            L = row[f'L_{i}']
            a = row[f'a_{i}']
            b = row[f'b_{i}']
            proportion = row[f'proportion_{i}']
            
            # Convert LAB to RGB for display
            r, g, b_val = lab_to_rgb(L, a, b)
            rgb_color = f'rgb({r}, {g}, {b_val})'
            
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
        height=400,  # Vous pouvez aussi augmenter la hauteur pour plus d'espace
        font=dict(family="Arial", size=12),
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.1,  # 🔥 Barres très épaisses
        bargroupgap=0.05,  # Espace minimal entre groupes
        margin=dict(l=80, r=80, t=80, b=80)  # Marges pour plus d'espace
    )
    
    # Correction: utiliser update_xaxes et update_yaxes (avec 's')
    fig.update_xaxes(gridcolor='lightgray')
    fig.update_yaxes(gridcolor='lightgray')
    
    return fig