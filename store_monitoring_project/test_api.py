import requests
import time
import sys
import os

def test_api():
    """
    Test the API endpoints
    """
    base_url = "http://localhost:8080"

    # Test trigger_report endpoint
    print("Testing trigger_report endpoint...")
    response = requests.post(f"{base_url}/trigger_report")
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        sys.exit(1)

    report_data = response.json()
    report_id = report_data.get('report_id')

    if not report_id:
        print("Error: No report_id returned")
        sys.exit(1)

    print(f"Report triggered with ID: {report_id}")

    # Test get_report endpoint
    print("Testing get_report endpoint...")
    max_attempts = 60  # Increase max attempts as report generation might take longer
    attempt = 0

    while attempt < max_attempts:
        response = requests.get(f"{base_url}/get_report?report_id={report_id}")

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            sys.exit(1)

        # Check if the report is still running
        if response.headers.get('Content-Type') == 'application/json':
            status = response.json().get('status')
            if status == 'Running':
                print(f"Report is still running. Waiting... (Attempt {attempt+1}/{max_attempts})")
                time.sleep(10)  # Wait 10 seconds before checking again
                attempt += 1
            else:
                print(f"Unexpected status: {status}")
                sys.exit(1)
        else:
            # Report is complete, we got the CSV file
            print("Report is complete. CSV file received.")

            # Create a reports directory if it doesn't exist
            os.makedirs('reports', exist_ok=True)

            # Save the CSV file
            report_path = os.path.join('reports', f"report_{report_id}.csv")
            with open(report_path, "wb") as f:
                f.write(response.content)

            print(f"Report saved to {report_path}")
            break

    if attempt >= max_attempts:
        print("Timeout waiting for report to complete")
        sys.exit(1)

    print("API test completed successfully")

if __name__ == "__main__":
    test_api()
