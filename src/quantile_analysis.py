"""Quantile-based grid sampling for hair color analysis"""
import pandas as pd
import numpy as np
from scipy.spatial.distance import euclidean
from config.settings import logger

def lab_to_lch(L, a, b):
    """Convert Lab to LCh (Lightness, Chroma, Hue)"""
    C = np.sqrt(a**2 + b**2)
    h = np.arctan2(b, a) * 180 / np.pi
    if h < 0:
        h += 360
    return L, C, h

def select_representative_samples_quantile(df_region, region_num, color_type='main', grid_size=4):
    """
    Select representative samples using quantile-based binning in LCh space
    
    Parameters:
    - df_region: DataFrame filtered for the region
    - region_num: Region number
    - color_type: 'main' or 'reflect'
    - grid_size: Number of bins per dimension (default 4 for 4x4)
    
    Returns:
    - Dictionary with selected samples for L-C and L-h grids
    """
    
    df = df_region.copy()
    
    # Convert all samples to LCh
    lch_data = []
    for idx, row in df.iterrows():
        L = row[f'L_{color_type}']
        a = row[f'a_{color_type}']
        b = row[f'b_{color_type}']
        
        L_val, C_val, h_val = lab_to_lch(L, a, b)
        
        lch_data.append({
            'index': idx,
            'RESP_FINAL': row['RESP_FINAL'],
            'VIDEOS': row['VIDEOS'],
            'XSHADE_S': row.get('XSHADE_S', ''),
            'L': L_val,
            'C': C_val,
            'h': h_val,
            'L_lab': L,
            'a_lab': a,
            'b_lab': b
        })
    
    df_lch = pd.DataFrame(lch_data)
    
    logger.info(f"Quantile-based sampling - Region {region_num} ({color_type})")
    logger.info(f"Total samples: {len(df_lch)}, Grid: {grid_size}x{grid_size}")
    
    # Calculate quantiles for L, C, h
    quantiles = [i/grid_size for i in range(grid_size + 1)]
    
    L_bins = df_lch['L'].quantile(quantiles).values
    C_bins = df_lch['C'].quantile(quantiles).values
    h_bins = df_lch['h'].quantile(quantiles).values
    
    # Assign grid cells for L-C space
    df_lch['L_bin'] = pd.cut(df_lch['L'], bins=L_bins, labels=False, include_lowest=True, duplicates='drop')
    df_lch['C_bin'] = pd.cut(df_lch['C'], bins=C_bins, labels=False, include_lowest=True, duplicates='drop')
    
    # Assign grid cells for L-h space
    df_lch['L_bin_h'] = pd.cut(df_lch['L'], bins=L_bins, labels=False, include_lowest=True, duplicates='drop')
    df_lch['h_bin'] = pd.cut(df_lch['h'], bins=h_bins, labels=False, include_lowest=True, duplicates='drop')
    
    # Select representative for each L-C grid cell
    selected_lc = []
    
    for L_idx in range(grid_size):
        for C_idx in range(grid_size):
            cell_samples = df_lch[(df_lch['L_bin'] == L_idx) & (df_lch['C_bin'] == C_idx)]
            
            if len(cell_samples) > 0:
                # Cell center
                L_center = (L_bins[L_idx] + L_bins[L_idx + 1]) / 2
                C_center = (C_bins[C_idx] + C_bins[C_idx + 1]) / 2
                
                # Find sample closest to cell center
                cell_samples['dist_to_center'] = cell_samples.apply(
                    lambda row: euclidean([row['L'], row['C']], [L_center, C_center]), 
                    axis=1
                )
                
                representative = cell_samples.loc[cell_samples['dist_to_center'].idxmin()]
                selected_lc.append(representative)
    
    # Select representative for each L-h grid cell
    selected_lh = []
    
    for L_idx in range(grid_size):
        for h_idx in range(grid_size):
            cell_samples = df_lch[(df_lch['L_bin_h'] == L_idx) & (df_lch['h_bin'] == h_idx)]
            
            if len(cell_samples) > 0:
                # Cell center
                L_center = (L_bins[L_idx] + L_bins[L_idx + 1]) / 2
                h_center = (h_bins[h_idx] + h_bins[h_idx + 1]) / 2
                
                # Find sample closest to cell center
                cell_samples['dist_to_center'] = cell_samples.apply(
                    lambda row: euclidean([row['L'], row['h']], [L_center, h_center]), 
                    axis=1
                )
                
                representative = cell_samples.loc[cell_samples['dist_to_center'].idxmin()]
                selected_lh.append(representative)
    
    df_selected_lc = pd.DataFrame(selected_lc)
    df_selected_lh = pd.DataFrame(selected_lh)
    
    logger.info(f"L-C Grid: {len(df_selected_lc)} samples, L-h Grid: {len(df_selected_lh)} samples")
    
    return {
        'lc_samples': df_selected_lc,
        'lh_samples': df_selected_lh,
        'bins': {
            'L': L_bins,
            'C': C_bins,
            'h': h_bins
        },
        'all_samples': df_lch
    }

def format_respondent_id(resp_final):
    """
    Convert RESP_FINAL to 4-digit format
    Handles both int and float inputs
    """
    try:
        resp_str = str(int(resp_final))
        # Pad with zeros if necessary to ensure 4 digits
        return resp_str.zfill(4)
    except:
        logger.warning(f"Could not convert RESP_FINAL to 4-digit format: {resp_final}")
        return None

def format_shade_name(videos):
    """
    Convert VIDEOS to shade name format
    Converts float to int to remove decimal point (77.0 → 77)
    """
    try:
        # Convert to int first to remove decimal, then to string
        return str(int(videos))
    except:
        logger.warning(f"Could not convert VIDEOS value to integer: {videos}")
        return None