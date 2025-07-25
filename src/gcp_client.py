"""GCP Storage client for accessing hair color data"""
import pandas as pd
import io
from PIL import Image
import streamlit as st
from config.settings import bucket, logger

def get_csv_from_gcs(blob_path: str) -> pd.DataFrame:
    """
    Download and read CSV file from GCS bucket
    
    Args:
        blob_path (str): Path to the CSV file in the bucket
        
    Returns:
        pd.DataFrame: DataFrame containing the CSV data
    """
    try:
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            logger.error(f"Blob {blob_path} does not exist")
            return pd.DataFrame()
        
        # Download as string and read with pandas
        csv_content = blob.download_as_string()
        df = pd.read_csv(io.StringIO(csv_content.decode('utf-8')))
        
        logger.info(f"Successfully loaded CSV from {blob_path}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading CSV from {blob_path}: {str(e)}")
        return pd.DataFrame()

def get_image_from_gcs(blob_path: str) -> Image.Image:
    """
    Download and load image file from GCS bucket
    
    Args:
        blob_path (str): Path to the image file in the bucket
        
    Returns:
        PIL.Image: Image object, or None if not found
    """
    try:
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            logger.error(f"Image blob {blob_path} does not exist")
            return None
        
        # Download image as bytes and load with PIL
        image_bytes = blob.download_as_bytes()
        image = Image.open(io.BytesIO(image_bytes))
        
        logger.info(f"Successfully loaded image from {blob_path}")
        return image
        
    except Exception as e:
        logger.error(f"Error loading image from {blob_path}: {str(e)}")
        return None

def get_mask_from_gcs(blob_path: str) -> Image.Image:
    """
    Download and load mask file from GCS bucket
    
    Args:
        blob_path (str): Path to the mask file in the bucket
        
    Returns:
        PIL.Image: Mask image object, or None if not found
    """
    try:
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            logger.error(f"Mask blob {blob_path} does not exist")
            return None
        
        # Download mask as bytes and load with PIL
        mask_bytes = blob.download_as_bytes()
        mask = Image.open(io.BytesIO(mask_bytes))
        
        logger.info(f"Successfully loaded mask from {blob_path}")
        return mask
        
    except Exception as e:
        logger.error(f"Error loading mask from {blob_path}: {str(e)}")
        return None

def find_swatch_in_folders(swatch_name_prefix: str, folders: list) -> tuple:
    """
    Find swatch image in the specified folders (dark, medium, light)
    
    Args:
        swatch_name_prefix (str): Prefix of the swatch filename
        folders (list): List of folder paths to search in
        
    Returns:
        tuple: (PIL.Image, found_path) or (None, None) if not found
    """
    from config.settings import SWATCHES_BASE_PATH
    
    for folder in folders:
        folder_path = f"{SWATCHES_BASE_PATH}/{folder}"
        swatch_filename = f"{swatch_name_prefix}.png"
        swatch_path = f"{folder_path}/{swatch_filename}"
        
        try:
            blob = bucket.blob(swatch_path)
            if blob.exists():
                image_bytes = blob.download_as_bytes()
                image = Image.open(io.BytesIO(image_bytes))
                logger.info(f"Found swatch: {swatch_path}")
                return image, swatch_path
        except Exception as e:
            logger.debug(f"Error checking swatch in {swatch_path}: {str(e)}")
            continue
    
    logger.warning(f"Swatch not found for prefix: {swatch_name_prefix}")
    return None, None

def check_blob_exists(blob_path: str) -> bool:
    """
    Check if a blob exists in the bucket
    
    Args:
        blob_path (str): Path to check
        
    Returns:
        bool: True if exists, False otherwise
    """
    try:
        blob = bucket.blob(blob_path)
        return blob.exists()
    except Exception as e:
        logger.error(f"Error checking blob existence {blob_path}: {str(e)}")
        return False