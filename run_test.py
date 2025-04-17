import os
import subprocess
import time
import sys

def run_test():
    """
    Run the application and test the API
    """
    # Check if the data files exist
    data_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'data')
    if not os.path.exists(os.path.join(data_dir, 'store_status.csv')):
        print("Data files not found. Running download_data.py...")
        subprocess.run([sys.executable, 'download_data.py'])
    
    # Start the application in a separate process
    print("Starting the application...")
    app_process = subprocess.Popen([sys.executable, 'run.py'])
    
    # Wait for the application to start
    print("Waiting for the application to start...")
    time.sleep(5)
    
    # Run the API test
    print("Running the API test...")
    try:
        subprocess.run([sys.executable, 'test_api.py'])
    finally:
        # Terminate the application process
        print("Terminating the application...")
        app_process.terminate()
        app_process.wait()

if __name__ == "__main__":
    run_test()
