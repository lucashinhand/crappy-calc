import google.cloud.storage as gcs
import os

# if you want abstraction you can go to a modern art museum lmao
# this will do for now

BUCKET_NAME = os.getenv("GCP_BUCKET_NAME", "your-bucket-name") 

def fetch_data_from_gcp_bucket(filename):
    client = gcs.Client()
    bucket = client.bucket(BUCKET_NAME)
    
    blob = bucket.blob(filename)
    if blob.exists():
        data_string = blob.download_as_text()
        return data_string
    return None

def save_data_to_gcp_bucket(data, filename, content_type='application/json'):
    # supported content types: 'application/json', 'text/csv'
    if content_type not in ['application/json', 'text/csv']:
        raise ValueError("Unsupported content type")

    client = gcs.Client()
    bucket = client.bucket(BUCKET_NAME)
    
    blob = bucket.blob(filename)
    blob.upload_from_string(data, content_type=content_type)
    return f"Data saved to {filename} in bucket {BUCKET_NAME}"