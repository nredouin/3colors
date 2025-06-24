"""Swatch loading utilities for hair color analysis"""
import pandas as pd
import os
from PIL import Image
from config.settings import SWATCH_FOLDERS, SHADES_MAPPING_CSV_PATH, logger
from src.gcp_client import find_swatch_in_folders

# Cache for shades mapping to avoid reloading
_shades_mapping_cache = None

def load_shades_mapping() -> pd.DataFrame:
    """
    Load the shades mapping CSV from local file with caching
    
    Returns:
        pd.DataFrame: Shades mapping data
    """
    global _shades_mapping_cache
    
    if _shades_mapping_cache is None:
        try:
            # Check if local file exists
            if not os.path.exists(SHADES_MAPPING_CSV_PATH):
                logger.error(f"Shades mapping CSV not found at: {SHADES_MAPPING_CSV_PATH}")
                _shades_mapping_cache = pd.DataFrame()
                return _shades_mapping_cache
            
            # Load CSV from local file
            _shades_mapping_cache = pd.read_csv(SHADES_MAPPING_CSV_PATH)
            logger.info(f"Loaded shades mapping from local file with {len(_shades_mapping_cache)} entries")
            
            # Log first few entries for debugging
            if not _shades_mapping_cache.empty:
                logger.info(f"Sample mapping entries:")
                for idx, row in _shades_mapping_cache.head(3).iterrows():
                    logger.info(f"  ID: {row['id']} -> Name: {row['Name_gcp_with_numberbyL']}")
            
        except Exception as e:
            logger.error(f"Error loading shades mapping from local file: {str(e)}")
            _shades_mapping_cache = pd.DataFrame()
    
    return _shades_mapping_cache

def get_swatch_name_for_shade(shade_id: str) -> str:
    """
    Get the swatch name prefix for a given shade ID
    
    Args:
        shade_id (str): The shade ID to look up
        
    Returns:
        str: Swatch name prefix or None if not found
    """
    mapping_df = load_shades_mapping()
    
    if mapping_df.empty:
        logger.warning("Shades mapping not available")
        return None
    
    # Convert shade_id to string and try different matching strategies
    shade_id_str = str(shade_id).strip()
    
    # Strategy 1: Exact string match
    matching_rows = mapping_df[mapping_df['id'].astype(str).str.strip() == shade_id_str]
    
    if not matching_rows.empty:
        swatch_name = matching_rows.iloc[0]['Name_gcp_with_numberbyL']
        logger.info(f"Found swatch name for shade {shade_id} (exact match): {swatch_name}")
        return swatch_name
    
    # Strategy 2: Try as integer if possible
    try:
        shade_id_int = int(shade_id_str)
        matching_rows = mapping_df[mapping_df['id'] == shade_id_int]
        
        if not matching_rows.empty:
            swatch_name = matching_rows.iloc[0]['Name_gcp_with_numberbyL']
            logger.info(f"Found swatch name for shade {shade_id} (integer match): {swatch_name}")
            return swatch_name
    except ValueError:
        pass
    
    # Strategy 3: Partial match (if shade_id is part of a larger identifier)
    partial_matches = mapping_df[mapping_df['id'].astype(str).str.contains(shade_id_str, na=False)]
    
    if not partial_matches.empty:
        swatch_name = partial_matches.iloc[0]['Name_gcp_with_numberbyL']
        logger.info(f"Found swatch name for shade {shade_id} (partial match): {swatch_name}")
        return swatch_name
    
    logger.warning(f"No swatch mapping found for shade ID: {shade_id}")
    
    # Log available IDs for debugging
    if not mapping_df.empty:
        available_ids = mapping_df['id'].head(10).tolist()
        logger.debug(f"Available shade IDs (first 10): {available_ids}")
    
    return None

def load_swatch_for_shade(shade_id: str) -> tuple:
    """
    Load swatch image for a given shade ID
    
    Args:
        shade_id (str): The shade ID
        
    Returns:
        tuple: (PIL.Image, swatch_info_dict) or (None, None) if not found
    """
    swatch_name = get_swatch_name_for_shade(shade_id)
    
    if not swatch_name:
        return None, None
    
    # Search in dark, medium, light folders
    swatch_image, found_path = find_swatch_in_folders(swatch_name, SWATCH_FOLDERS)
    
    if swatch_image:
        # Extract folder name from path
        folder_name = found_path.split('/')[-2] if '/' in found_path else "unknown"
        
        swatch_info = {
            'name': swatch_name,
            'path': found_path,
            'folder': folder_name,
            'filename': f"{swatch_name}.png"
        }
        
        logger.info(f"Successfully loaded swatch for shade {shade_id} from {folder_name}")
        return swatch_image, swatch_info
    
    return None, None

def extract_shade_id_from_data(df: pd.DataFrame) -> str:
    """
    Extract shade ID from the color data DataFrame
    
    Args:
        df (pd.DataFrame): Color data DataFrame
        
    Returns:
        str: Shade ID if found, None otherwise
    """
    # Look for common column names that might contain the shade ID
    possible_columns = ['shade', 'shade_id', 'id', 'XSHADES', 'id_x']
    
    for col in possible_columns:
        if col in df.columns:
            # Get the first non-null value
            shade_values = df[col].dropna().unique()
            if len(shade_values) > 0:
                shade_id = str(shade_values[0])
                logger.info(f"Found shade ID '{shade_id}' in column '{col}'")
                return shade_id
    
    logger.warning("No shade ID found in data")
    logger.debug(f"Available columns: {df.columns.tolist()}")
    
    return None

def reload_shades_mapping():
    """
    Force reload of the shades mapping (useful for testing)
    """
    global _shades_mapping_cache
    _shades_mapping_cache = None
    return load_shades_mapping()

def get_mapping_info() -> dict:
    """
    Get information about the current mapping
    
    Returns:
        dict: Information about the mapping file
    """
    info = {
        'file_path': SHADES_MAPPING_CSV_PATH,
        'file_exists': os.path.exists(SHADES_MAPPING_CSV_PATH),
        'total_entries': 0,
        'sample_entries': []
    }
    
    mapping_df = load_shades_mapping()
    if not mapping_df.empty:
        info['total_entries'] = len(mapping_df)
        info['sample_entries'] = [
            {'id': row['id'], 'name': row['Name_gcp_with_numberbyL']} 
            for _, row in mapping_df.head(5).iterrows()
        ]
    
    return info