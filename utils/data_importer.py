import pandas as pd
from app.models.models import StoreStatus, BusinessHours, StoreTimezone
from app import db
from datetime import datetime
import os
import traceback

def import_data():
    """
    Import data from CSV files into the database
    """
    app_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(app_dir, 'data')

    # Import store status data
    status_file = os.path.join(data_dir, 'store_status.csv')
    if os.path.exists(status_file):
        print(f"Importing store status data from {status_file}")
        # Read in chunks to handle large files
        for chunk in pd.read_csv(status_file, chunksize=10000):
            for _, row in chunk.iterrows():
                try:
                    # Parse the timestamp - handle different possible formats
                    timestamp_str = row['timestamp_utc']
                    if ' UTC' in timestamp_str:
                        timestamp_str = timestamp_str.replace(' UTC', '')

                    # Try different timestamp formats
                    try:
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        try:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            print(f"Could not parse timestamp: {timestamp_str}")
                            continue

                    status = StoreStatus(
                        store_id=row['store_id'],
                        status=row['status'],
                        timestamp_utc=timestamp
                    )
                    db.session.add(status)
                except Exception as e:
                    print(f"Error processing row: {row}")
                    print(f"Error: {e}")
                    traceback.print_exc()
            db.session.commit()

    # Import business hours data
    hours_file = os.path.join(data_dir, 'menu_hours.csv')
    if os.path.exists(hours_file):
        print(f"Importing business hours data from {hours_file}")
        for chunk in pd.read_csv(hours_file, chunksize=10000):
            for _, row in chunk.iterrows():
                # Parse the times
                start_time = datetime.strptime(row['start_time_local'], '%H:%M:%S').time()
                end_time = datetime.strptime(row['end_time_local'], '%H:%M:%S').time()
                hours = BusinessHours(
                    store_id=row['store_id'],
                    day_of_week=int(row['dayOfWeek']),
                    start_time_local=start_time,
                    end_time_local=end_time
                )
                db.session.add(hours)
            db.session.commit()

    # Import timezone data
    timezone_file = os.path.join(data_dir, 'timezones.csv')
    if os.path.exists(timezone_file):
        print(f"Importing timezone data from {timezone_file}")
        for chunk in pd.read_csv(timezone_file, chunksize=10000):
            for _, row in chunk.iterrows():
                timezone = StoreTimezone(
                    store_id=row['store_id'],
                    timezone_str=row['timezone_str']
                )
                db.session.add(timezone)
            db.session.commit()

    print("Data import complete")
