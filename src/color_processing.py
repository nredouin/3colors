"""Color processing utilities for hair color remapping"""
import numpy as np
import pandas as pd
from PIL import Image
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

def get_sample_info(df: pd.DataFrame) -> list:
    """
    Get information about all samples for selection
    
    Args:
        df (pd.DataFrame): Color data DataFrame
        
    Returns:
        list: List of sample information dictionaries
    """
    samples_info = []
    
    for idx, row in df.iterrows():
        # Calculate balance score (how far from 33.33% each)
        proportions = [row[f'proportion_{i+1}'] for i in range(3)]
        target_proportion = 100.0 / 3  # 33.33%
        balance_score = sum(abs(prop - target_proportion) for prop in proportions)
        
        # Get filename
        filename = row.get('filename', f'Sample {idx+1}')
        
        sample_info = {
            'index': idx,
            'filename': filename,
            'proportions': proportions,
            'balance_score': balance_score,
            'display_name': f"Sample {idx+1}: {filename}" if filename != f'Sample {idx+1}' else f"Sample {idx+1}"
        }
        
        samples_info.append(sample_info)
    
    return samples_info

def find_closest_color(pixel_rgb, cluster_centers):
    """
    Find the closest color in cluster_centers to pixel_rgb
    
    Args:
        pixel_rgb: RGB values of the pixel
        cluster_centers: Array of RGB cluster centers
        
    Returns:
        Closest RGB color from cluster centers
    """
    pixel_rgb = np.array(pixel_rgb)
    distances = np.linalg.norm(cluster_centers - pixel_rgb, axis=1)
    closest_index = np.argmin(distances)
    return cluster_centers[closest_index]

def remap_hair_colors(image: Image.Image, mask: Image.Image, color_data: pd.Series, n_clusters: int = 3) -> Image.Image:
    """
    Remap hair colors using the closest cluster colors from LAB data
    
    Args:
        image (PIL.Image): Original hair image
        mask (PIL.Image): Hair mask
        color_data (pd.Series): Row of color data with LAB values
        n_clusters (int): Number of color clusters
        
    Returns:
        PIL.Image: Remapped image
    """
    try:
        # Convert images to RGB if not already
        image = image.convert("RGB")
        mask = mask.convert("RGB")
        
        # Check size compatibility
        if image.size != mask.size:
            logger.error(f"Image and mask size mismatch: {image.size} vs {mask.size}")
            return image
        
        # Convert to numpy arrays
        image_np = np.array(image)
        mask_np = np.array(mask)
        
        # Create mask for non-black pixels (hair areas)
        non_black_mask = (mask_np != [0, 0, 0]).all(axis=2)
        
        # Extract cluster centers from LAB data and convert to RGB using luxpy
        cluster_centers = []
        for i in range(n_clusters):
            L = color_data[f'L_{i+1}']
            a = color_data[f'a_{i+1}']
            b = color_data[f'b_{i+1}']
            
            # Convert LAB to RGB using luxpy
            lab_values = [L, a, b]
            rgb_values = lab_to_rgb(lab_values)
            cluster_centers.append(rgb_values)
            
            logger.info(f"Cluster {i+1}: LAB({L:.1f}, {a:.1f}, {b:.1f}) -> RGB({rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]})")
        
        cluster_centers = np.array(cluster_centers).astype(int)
        
        # Apply color remapping only to hair pixels
        indices = np.where(non_black_mask)
        total_pixels = len(indices[0])
        
        logger.info(f"Starting color remapping for {total_pixels} hair pixels...")
        
        for i, (y, x) in enumerate(zip(indices[0], indices[1])):
            original_rgb = image_np[y, x]
            closest_rgb = find_closest_color(original_rgb, cluster_centers)
            image_np[y, x] = closest_rgb
            
            # Log progress for large images
            if i % 20000 == 0 and i > 0:
                logger.info(f"Processed {i}/{total_pixels} pixels ({100*i/total_pixels:.1f}%)")
        
        # Create remapped image
        remapped_image = Image.fromarray(image_np)
        logger.info(f"Successfully remapped {total_pixels} hair pixels with {n_clusters} colors")
        
        return remapped_image
        
    except Exception as e:
        logger.error(f"Error in color remapping: {str(e)}")
        return image

def process_hair_color_remapping_with_sample(image: Image.Image, mask: Image.Image, df: pd.DataFrame, sample_index: int) -> Image.Image:
    """
    Process hair color remapping with a specific selected sample
    
    Args:
        image (PIL.Image): Original hair image
        mask (PIL.Image): Hair mask
        df (pd.DataFrame): Color data DataFrame
        sample_index (int): Index of the sample to use for remapping
        
    Returns:
        PIL.Image: Remapped image
    """
    if df.empty or image is None or mask is None:
        logger.warning("Missing data for color remapping")
        return image
    
    if sample_index >= len(df) or sample_index < 0:
        logger.error(f"Invalid sample index {sample_index}. DataFrame has {len(df)} rows.")
        return image
    
    # Get the selected sample
    selected_sample = df.iloc[sample_index]
    
    # Log selected sample info
    filename = selected_sample.get('filename', f'Sample {sample_index+1}')
    proportions = [selected_sample[f'proportion_{i+1}'] for i in range(3)]
    logger.info(f"Using selected sample {sample_index+1}: {filename}")
    logger.info(f"Color proportions: {proportions}")
    
    # Perform color remapping
    remapped_image = remap_hair_colors(image, mask, selected_sample, n_clusters=3)
    
    return remapped_image