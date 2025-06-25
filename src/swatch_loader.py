"""Swatch loading utilities for hair color analysis with category-based mapping"""
import pandas as pd
import os
from PIL import Image
from config.settings import SHADES_MAPPING_CSV_PATH, HAIR_CATEGORY_CSV_PATH, SWATCHES_BASE_PATH, logger
from src.gcp_client import get_image_from_gcs

# Cache for CSV files to avoid reloading
_shades_mapping_cache = None
_hair_category_cache = None

def load_shades_mapping() -> pd.DataFrame:
    """
    Load the shades mapping CSV from local file with caching
    
    Returns:
        pd.DataFrame: Shades mapping data with columns Number_light, Number_medium, Number_dark, Name_gcp_with_numberbyL
    """
    global _shades_mapping_cache
    
    if _shades_mapping_cache is None:
        try:
            if not os.path.exists(SHADES_MAPPING_CSV_PATH):
                logger.error(f"Shades mapping CSV not found at: {SHADES_MAPPING_CSV_PATH}")
                _shades_mapping_cache = pd.DataFrame()
                return _shades_mapping_cache
            
            # Try both comma and semicolon separators
            try:
                _shades_mapping_cache = pd.read_csv(SHADES_MAPPING_CSV_PATH, sep=',')
            except:
                _shades_mapping_cache = pd.read_csv(SHADES_MAPPING_CSV_PATH, sep=';')
            
            logger.info(f"Loaded shades mapping from local file with {len(_shades_mapping_cache)} entries")
            
            # Log sample entries for debugging
            if not _shades_mapping_cache.empty:
                logger.info("Sample shades mapping entries:")
                for idx, row in _shades_mapping_cache.head(3).iterrows():
                    logger.info(f"  Name: {row['Name_gcp_with_numberbyL']}")
                    logger.info(f"    Light: {row.get('Number_light', 'N/A')}, Medium: {row.get('Number_medium', 'N/A')}, Dark: {row.get('Number_dark', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error loading shades mapping: {str(e)}")
            _shades_mapping_cache = pd.DataFrame()
    
    return _shades_mapping_cache

def load_hair_category() -> pd.DataFrame:
    """
    Load the hair category CSV from local file with caching
    Supports both comma and semicolon separators
    
    Returns:
        pd.DataFrame: Hair category data with RESP_FINAL and CATEGORY columns
    """
    global _hair_category_cache
    
    if _hair_category_cache is None:
        try:
            if not os.path.exists(HAIR_CATEGORY_CSV_PATH):
                logger.error(f"Hair category CSV not found at: {HAIR_CATEGORY_CSV_PATH}")
                _hair_category_cache = pd.DataFrame()
                return _hair_category_cache
            
            # Try semicolon separator first (based on your format), then comma
            try:
                _hair_category_cache = pd.read_csv(HAIR_CATEGORY_CSV_PATH, sep=';')
                logger.info("Loaded hair category CSV with semicolon separator")
            except:
                _hair_category_cache = pd.read_csv(HAIR_CATEGORY_CSV_PATH, sep=',')
                logger.info("Loaded hair category CSV with comma separator")
            
            logger.info(f"Loaded hair category mapping with {len(_hair_category_cache)} entries")
            
            # Log sample entries for debugging
            if not _hair_category_cache.empty:
                logger.info("Sample hair category entries:")
                logger.info(f"Columns found: {_hair_category_cache.columns.tolist()}")
                for idx, row in _hair_category_cache.head(3).iterrows():
                    # Handle different possible column names
                    resp_id = None
                    category = None
                    
                    # Try different column names for respondent ID
                    for col in ['RESP_FINAL', 'Respondent ID', 'respondent_id', 'filename', 'id']:
                        if col in row:
                            resp_id = row[col]
                            break
                    
                    # Try different column names for category
                    for col in ['CATEGORY', 'Category', 'category']:
                        if col in row:
                            category = row[col]
                            break
                    
                    logger.info(f"  {resp_id} -> {category}")
            
        except Exception as e:
            logger.error(f"Error loading hair category mapping: {str(e)}")
            _hair_category_cache = pd.DataFrame()
    
    return _hair_category_cache

def get_category_for_respondent(respondent_id: str) -> str:
    """
    Get the hair category (dark/medium/light) for a given respondent ID
    
    Args:
        respondent_id (str): The respondent ID to look up
        
    Returns:
        str: Category (dark/medium/light) or None if not found
    """
    category_df = load_hair_category()
    
    if category_df.empty:
        logger.warning("Hair category mapping not available")
        return None
    
    # Try different column names for respondent ID (prioritize RESP_FINAL)
    possible_id_columns = ['RESP_FINAL', 'Respondent ID', 'respondent_id', 'filename', 'id']
    # Try different column names for category
    possible_category_columns = ['CATEGORY', 'Category', 'category']
    
    respondent_id_str = str(respondent_id).strip()
    
    for id_col in possible_id_columns:
        if id_col in category_df.columns:
            # Try exact match
            matching_rows = category_df[category_df[id_col].astype(str).str.strip() == respondent_id_str]
            
            if not matching_rows.empty:
                # Find the category column
                category = None
                for cat_col in possible_category_columns:
                    if cat_col in matching_rows.columns:
                        category = matching_rows.iloc[0][cat_col].lower().strip()
                        logger.info(f"Found category for respondent {respondent_id}: {category} (using columns {id_col} -> {cat_col})")
                        return category
                
                if category is None:
                    logger.error(f"Found respondent {respondent_id} but no category column found")
                    return None
            
            # Try partial match (if respondent_id is part of filename)
            partial_matches = category_df[category_df[id_col].astype(str).str.contains(respondent_id_str, na=False)]
            
            if not partial_matches.empty:
                # Find the category column
                category = None
                for cat_col in possible_category_columns:
                    if cat_col in partial_matches.columns:
                        category = partial_matches.iloc[0][cat_col].lower().strip()
                        logger.info(f"Found category for respondent {respondent_id} (partial match): {category}")
                        return category
    
    logger.warning(f"No category found for respondent ID: {respondent_id}")
    
    # Log available respondent IDs for debugging
    if not category_df.empty:
        for id_col in possible_id_columns:
            if id_col in category_df.columns:
                available_ids = category_df[id_col].head(10).tolist()
                logger.debug(f"Available respondent IDs in column '{id_col}' (first 10): {available_ids}")
                break
    
    return None

def get_swatch_name_for_shade_and_category(shade_id: str, category: str) -> str:
    """
    Get the swatch name for a given shade ID and category
    
    Args:
        shade_id (str): The shade ID to look up
        category (str): The category (dark/medium/light)
        
    Returns:
        str: Swatch name prefix or None if not found
    """
    mapping_df = load_shades_mapping()
    
    if mapping_df.empty:
        logger.warning("Shades mapping not available")
        return None
    
    # Determine which column to search based on category
    category_lower = category.lower().strip()
    if category_lower == 'dark':
        number_column = 'Number_dark'
    elif category_lower == 'medium':
        number_column = 'Number_medium'
    elif category_lower == 'light':
        number_column = 'Number_light'
    else:
        logger.error(f"Invalid category: {category}. Must be dark, medium, or light")
        return None
    
    # Convert shade_id to different types for matching
    shade_id_str = str(shade_id).strip()
    
    try:
        shade_id_int = int(shade_id_str)
        
        # Look for rows where the number_column matches the shade_id
        matching_rows = mapping_df[mapping_df[number_column] == shade_id_int]
        
        if not matching_rows.empty:
            swatch_name = matching_rows.iloc[0]['Name_gcp_with_numberbyL']
            logger.info(f"Found swatch name for shade {shade_id} in category {category}: {swatch_name}")
            return swatch_name
        
    except ValueError:
        logger.warning(f"Could not convert shade_id '{shade_id}' to integer for matching")
    
    # Try string matching as fallback
    matching_rows = mapping_df[mapping_df[number_column].astype(str).str.strip() == shade_id_str]
    
    if not matching_rows.empty:
        swatch_name = matching_rows.iloc[0]['Name_gcp_with_numberbyL']
        logger.info(f"Found swatch name for shade {shade_id} in category {category} (string match): {swatch_name}")
        return swatch_name
    
    logger.warning(f"No swatch mapping found for shade ID {shade_id} in category {category}")
    
    # Log available numbers in that category for debugging
    available_numbers = mapping_df[mapping_df[number_column].notna()][number_column].head(10).tolist()
    logger.debug(f"Available {category} numbers (first 10): {available_numbers}")
    
    return None

def load_swatch_from_category_folder(swatch_name: str, category: str, swatch_id: str) -> tuple:
    """
    Load swatch image from the specific category folder
    
    Args:
        swatch_name (str): Swatch name prefix
        category (str): Category (dark/medium/light)
        swatch_id (str): Swatch ID to include in filename
        
    Returns:
        tuple: (PIL.Image, swatch_info_dict) or (None, None) if not found
    """
    category_lower = category.lower().strip()
    
    # Build the path to the swatch with swatch_id prefix
    swatch_filename = f"{swatch_name}.png"
    swatch_path = f"{SWATCHES_BASE_PATH}/{category_lower}/{swatch_id}_{swatch_filename}"
    
    try:
        swatch_image = get_image_from_gcs(swatch_path)
        
        if swatch_image:
            swatch_info = {
                'name': swatch_name,
                'path': swatch_path,
                'folder': category_lower,
                'filename': f"{swatch_id}_{swatch_filename}",
                'category': category_lower,
                'swatch_id': swatch_id
            }
            
            logger.info(f"Successfully loaded swatch from {category_lower} folder: {swatch_path}")
            return swatch_image, swatch_info
        
    except Exception as e:
        logger.error(f"Error loading swatch from {swatch_path}: {str(e)}")
    
    logger.warning(f"Swatch not found: {swatch_path}")
    return None, None

def load_swatch_for_respondent_and_shade(respondent_id: str, shade_id: str) -> tuple:
    """
    Load swatch image for a given respondent ID and shade ID using the two-step mapping
    
    Args:
        respondent_id (str): The respondent ID
        shade_id (str): The shade ID
        
    Returns:
        tuple: (PIL.Image, swatch_info_dict) or (None, None) if not found
    """
    # Step 1: Get category for respondent
    category = get_category_for_respondent(respondent_id)
    
    if not category:
        logger.warning(f"Could not determine category for respondent {respondent_id}")
        return None, None
    
    # Step 2: Get swatch name for shade and category
    swatch_name = get_swatch_name_for_shade_and_category(shade_id, category)
    
    if not swatch_name:
        logger.warning(f"Could not find swatch name for shade {shade_id} in category {category}")
        return None, None
    
    # Step 3: Load swatch from the appropriate folder with swatch_id in filename
    swatch_image, swatch_info = load_swatch_from_category_folder(swatch_name, category, shade_id)
    
    if swatch_image and swatch_info:
        # Add extra info about the mapping process
        swatch_info['respondent_id'] = respondent_id
        swatch_info['shade_id'] = shade_id
        swatch_info['mapping_category'] = category
        
        logger.info(f"Successfully loaded swatch for respondent {respondent_id}, shade {shade_id}: {swatch_name}")
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

def reload_mappings():
    """
    Force reload of both mapping CSV files (useful for testing)
    """
    global _shades_mapping_cache, _hair_category_cache
    _shades_mapping_cache = None
    _hair_category_cache = None
    
    shades_df = load_shades_mapping()
    category_df = load_hair_category()
    
    return len(shades_df), len(category_df)

def get_mapping_info() -> dict:
    """
    Get information about both mapping files
    
    Returns:
        dict: Information about both mapping files
    """
    info = {
        'shades_mapping': {
            'file_path': SHADES_MAPPING_CSV_PATH,
            'file_exists': os.path.exists(SHADES_MAPPING_CSV_PATH),
            'total_entries': 0,
            'sample_entries': []
        },
        'hair_category': {
            'file_path': HAIR_CATEGORY_CSV_PATH,
            'file_exists': os.path.exists(HAIR_CATEGORY_CSV_PATH),
            'total_entries': 0,
            'sample_entries': [],
            'columns': []
        }
    }
    
    # Shades mapping info
    shades_df = load_shades_mapping()
    if not shades_df.empty:
        info['shades_mapping']['total_entries'] = len(shades_df)
        info['shades_mapping']['sample_entries'] = [
            {
                'name': row['Name_gcp_with_numberbyL'],
                'light': row.get('Number_light', 'N/A'),
                'medium': row.get('Number_medium', 'N/A'),
                'dark': row.get('Number_dark', 'N/A')
            }
            for _, row in shades_df.head(3).iterrows()
        ]
    
    # Hair category info
    category_df = load_hair_category()
    if not category_df.empty:
        info['hair_category']['total_entries'] = len(category_df)
        info['hair_category']['columns'] = category_df.columns.tolist()
        
        # Find the correct column names
        resp_col = None
        cat_col = None
        a1r_col = None
        
        for col in ['RESP_FINAL', 'Respondent ID', 'respondent_id', 'filename', 'id']:
            if col in category_df.columns:
                resp_col = col
                break
        
        for col in ['CATEGORY', 'Category', 'category']:
            if col in category_df.columns:
                cat_col = col
                break
                
        for col in ['A1R', 'a1r', 'A1r', 'skin_tone_cluster']:
            if col in category_df.columns:
                a1r_col = col
                break
        
        if resp_col and cat_col:
            info['hair_category']['sample_entries'] = [
                {
                    'respondent_id': row[resp_col],
                    'category': row[cat_col],
                    'skin_tone_cluster': row.get(a1r_col, 'N/A') if a1r_col else 'N/A'
                }
                for _, row in category_df.head(3).iterrows()
            ]
    
    return info


def get_respondent_info(respondent_id: str) -> dict:
    """
    Get comprehensive information for a given respondent ID including hair tone and skin tone cluster
    
    Args:
        respondent_id (str): The respondent ID to look up
        
    Returns:
        dict: Dictionary with hair_tone, skin_tone_cluster, and found status
    """
    category_df = load_hair_category()
    
    result = {
        'hair_tone': None,
        'skin_tone_cluster': None,
        'found': False
    }
    
    if category_df.empty:
        logger.warning("Hair category mapping not available")
        return result
    
    # Try different column names for respondent ID
    possible_id_columns = ['RESP_FINAL', 'Respondent ID', 'respondent_id', 'filename', 'id']
    # Try different column names for category (hair tone)
    possible_category_columns = ['CATEGORY', 'Category', 'category']
    # Try different column names for A1R (skin tone cluster)
    possible_a1r_columns = ['A1R', 'a1r', 'A1r', 'skin_tone_cluster']
    
    respondent_id_str = str(respondent_id).strip()
    
    for id_col in possible_id_columns:
        if id_col in category_df.columns:
            # Try exact match
            matching_rows = category_df[category_df[id_col].astype(str).str.strip() == respondent_id_str]
            
            if not matching_rows.empty:
                row = matching_rows.iloc[0]
                result['found'] = True
                
                # Get hair tone (category)
                for cat_col in possible_category_columns:
                    if cat_col in row and pd.notna(row[cat_col]):
                        result['hair_tone'] = str(row[cat_col]).strip().title()
                        break
                
                # Get skin tone cluster (A1R)
                for a1r_col in possible_a1r_columns:
                    if a1r_col in row and pd.notna(row[a1r_col]):
                        result['skin_tone_cluster'] = str(row[a1r_col]).strip()
                        break
                
                logger.info(f"Found info for respondent {respondent_id}: Hair Tone={result['hair_tone']}, Skin Tone Cluster={result['skin_tone_cluster']}")
                return result
            
            # Try partial match (if respondent_id is part of filename)
            partial_matches = category_df[category_df[id_col].astype(str).str.contains(respondent_id_str, na=False)]
            
            if not partial_matches.empty:
                row = partial_matches.iloc[0]
                result['found'] = True
                
                # Get hair tone (category)
                for cat_col in possible_category_columns:
                    if cat_col in row and pd.notna(row[cat_col]):
                        result['hair_tone'] = str(row[cat_col]).strip().title()
                        break
                
                # Get skin tone cluster (A1R)
                for a1r_col in possible_a1r_columns:
                    if a1r_col in row and pd.notna(row[a1r_col]):
                        result['skin_tone_cluster'] = str(row[a1r_col]).strip()
                        break
                
                logger.info(f"Found info for respondent {respondent_id} (partial match): Hair Tone={result['hair_tone']}, Skin Tone Cluster={result['skin_tone_cluster']}")
                return result
    
    logger.warning(f"No information found for respondent ID: {respondent_id}")
    return result