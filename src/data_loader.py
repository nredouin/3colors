"""Data loading utilities for hair color analysis"""
import pandas as pd
from PIL import Image
from config.settings import CITY_FOLDERS, CSV_PATH_TEMPLATE, logger
from src.gcp_client import get_csv_from_gcs, get_image_from_gcs, get_mask_from_gcs

def get_city_from_id(respondent_id: str) -> int:
    """
    Extract city code from respondent ID
    
    Args:
        respondent_id (str): 4-digit respondent ID
        
    Returns:
        int: City code (1-7)
    """
    if len(respondent_id) != 4:
        raise ValueError("Respondent ID must be 4 digits")
    
    city_code = int(respondent_id[0])
    if city_code not in CITY_FOLDERS:
        raise ValueError(f"Invalid city code: {city_code}")
    
    return city_code

def build_csv_path(respondent_id: str) -> str:
    """
    Build the GCS path to the CSV file for a given respondent ID
    
    Args:
        respondent_id (str): 4-digit respondent ID
        
    Returns:
        str: GCS path to the CSV file
    """
    city_code = get_city_from_id(respondent_id)
    city_folder = CITY_FOLDERS[city_code]
    
    csv_path = CSV_PATH_TEMPLATE.format(
        city_folder=city_folder,
        id=respondent_id
    )
    
    return csv_path

def build_image_path(respondent_id: str, shade: str) -> str:
    """
    Build the GCS path to the image file for a given respondent ID and shade
    
    Args:
        respondent_id (str): 4-digit respondent ID
        shade (str): Hair shade
        
    Returns:
        str: GCS path to the image file
    """
    city_code = get_city_from_id(respondent_id)
    city_folder = CITY_FOLDERS[city_code]
    
    image_path = f"{city_folder}/processed/results/images/{respondent_id}/{shade}/{respondent_id}03_{shade}.png"
    
    return image_path

def build_mask_path(respondent_id: str, shade: str) -> str:
    """
    Build the GCS path to the mask file for a given respondent ID and shade
    
    Args:
        respondent_id (str): 4-digit respondent ID
        shade (str): Hair shade
        
    Returns:
        str: GCS path to the mask file
    """
    city_code = get_city_from_id(respondent_id)
    city_folder = CITY_FOLDERS[city_code]
    
    mask_path = f"{city_folder}/processed/results/masksV3/{respondent_id}/{shade}/{respondent_id}03_{shade}_mask.png"
    
    return mask_path

def load_respondent_data(respondent_id: str, shade: str = None) -> pd.DataFrame:
    """
    Load hair color data for a specific respondent
    
    Args:
        respondent_id (str): 4-digit respondent ID
        shade (str, optional): Specific shade to filter. If None, returns all shades
        
    Returns:
        pd.DataFrame: Hair color data
    """
    try:
        csv_path = build_csv_path(respondent_id)
        df = get_csv_from_gcs(csv_path)
        
        if df.empty:
            logger.warning(f"No data found for respondent {respondent_id}")
            return df
        
        # Filter by shade if specified
        if shade:
            df = df[df['shade'] == shade]
            if df.empty:
                logger.warning(f"No data found for respondent {respondent_id} with shade {shade}")
        
        # Take only first 5 rows
        df = df.head(5)
        
        logger.info(f"Loaded {len(df)} rows for respondent {respondent_id}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading data for respondent {respondent_id}: {str(e)}")
        return pd.DataFrame()

def load_respondent_image(respondent_id: str, shade: str) -> Image.Image:
    """
    Load hair color image for a specific respondent and shade
    
    Args:
        respondent_id (str): 4-digit respondent ID
        shade (str): Hair shade
        
    Returns:
        PIL.Image: Image object, or None if not found
    """
    try:
        image_path = build_image_path(respondent_id, shade)
        image = get_image_from_gcs(image_path)
        
        if image:
            logger.info(f"Successfully loaded image for respondent {respondent_id}, shade {shade}")
        else:
            logger.warning(f"No image found for respondent {respondent_id}, shade {shade}")
        
        return image
        
    except Exception as e:
        logger.error(f"Error loading image for respondent {respondent_id}, shade {shade}: {str(e)}")
        return None

def load_respondent_mask(respondent_id: str, shade: str) -> Image.Image:
    """
    Load hair mask for a specific respondent and shade
    
    Args:
        respondent_id (str): 4-digit respondent ID
        shade (str): Hair shade
        
    Returns:
        PIL.Image: Mask image object, or None if not found
    """
    try:
        mask_path = build_mask_path(respondent_id, shade)
        mask = get_mask_from_gcs(mask_path)
        
        if mask:
            logger.info(f"Successfully loaded mask for respondent {respondent_id}, shade {shade}")
        else:
            logger.warning(f"No mask found for respondent {respondent_id}, shade {shade}")
        
        return mask
        
    except Exception as e:
        logger.error(f"Error loading mask for respondent {respondent_id}, shade {shade}: {str(e)}")
        return None

def get_available_shades(respondent_id: str) -> list:
    """
    Get list of available shades for a respondent
    
    Args:
        respondent_id (str): 4-digit respondent ID
        
    Returns:
        list: List of available shades
    """
    try:
        csv_path = build_csv_path(respondent_id)
        df = get_csv_from_gcs(csv_path)
        
        if df.empty:
            return []
        
        return sorted(df['shade'].unique().tolist())
        
    except Exception as e:
        logger.error(f"Error getting shades for respondent {respondent_id}: {str(e)}")
        return []