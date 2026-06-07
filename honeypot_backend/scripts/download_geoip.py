import os
import sys
from google.cloud import storage
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_geoip():
    bucket_name = os.environ.get("GEOIP_BUCKET_NAME", "honeypot-soc-geoip-us-central1")
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    city_path = os.path.join(data_dir, "GeoLite2-City.mmdb")
    asn_path = os.path.join(data_dir, "GeoLite2-ASN.mmdb")
    
    if os.path.exists(city_path) and os.path.exists(asn_path):
        logger.info("GeoIP databases already exist locally. Skipping download.")
        return

    try:
        logger.info(f"Downloading GeoIP databases from gs://{bucket_name}...")
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        for file_name in ["GeoLite2-City.mmdb", "GeoLite2-ASN.mmdb"]:
            blob = bucket.blob(file_name)
            dest_path = os.path.join(data_dir, file_name)
            if not os.path.exists(dest_path):
                blob.download_to_filename(dest_path)
                logger.info(f"Successfully downloaded {file_name}")
                
    except Exception as e:
        logger.error(f"Failed to download GeoIP databases: {e}")
        logger.info("Application will start but GeoIP lookups may fail.")

if __name__ == "__main__":
    download_geoip()
