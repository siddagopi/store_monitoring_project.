import os
import requests
import zipfile
import io

def download_data():
    """
    Download the data files from the provided URL and extract them to the app/data directory
    """
    url = "https://storage.googleapis.com/hiring-problem-statements/store-monitoring-data.zip"
    data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'data')
    
    # Create the data directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"Downloading data from {url}...")
    response = requests.get(url)
    
    if response.status_code == 200:
        print("Download complete. Extracting files...")
        
        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(data_dir)
        
        print(f"Files extracted to {data_dir}")
    else:
        print(f"Error downloading data: {response.status_code}")

if __name__ == "__main__":
    download_data()
