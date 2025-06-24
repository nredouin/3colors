""" Configuration file for the Hair Color Analysis App """
import logging
import multiprocessing
import torch
from google.cloud import storage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global device setting
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# GCS bucket configuration
BUCKET_NAME = "mcb-hair-bucket"
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

# City folders mapping
CITY_FOLDERS = { 
    1: "mcb_hair_bucket_freehold",
    2: "mcb_hair_bucket_tampa",
    3: "mcb_hair_bucket_chicago",
    4: "mcb_hair_bucket_losangeles",
    5: "mcb_hair_bucket_atlanta",
    6: "mcb_hair_bucket_miami",
    7: "mcb_hair_bucket_dallas",
}

# Image format
IMAGE_FORMAT = 'PNG'

# CPU count for optimization
NB_VCPU = multiprocessing.cpu_count()

# CSV path template
CSV_PATH_TEMPLATE = "{city_folder}/processed/results/color_extraction3/{id}.csv"

# Swatches configuration
SWATCHES_BASE_PATH = "mcb_hair_bucket_atlanta/swatches"
SWATCH_FOLDERS = ["dark", "medium", "light"]  # Search order

# Shades mapping CSV path (LOCAL FILE)
SHADES_MAPPING_CSV_PATH = "data/shades_mapping.csv"  # Local path - update as needed