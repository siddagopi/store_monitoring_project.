import pandas as pd
import numpy as np
from app.models.models import StoreStatus, BusinessHours, StoreTimezone, Report
from app import db, create_app
from datetime import datetime, timedelta, time
import pytz
import os
from sqlalchemy import func, distinct

def generate_report(report_id):
    """
    Generate a report with uptime and downtime metrics for all stores
    """
    # Create app context
    app = create_app()
    with app.app_context():
        try:
            # Create reports directory if it doesn't exist
            app_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
            reports_dir = os.path.join(app_dir, 'reports')
            os.makedirs(reports_dir, exist_ok=True)

            # Define the output file path
            output_file = os.path.join(reports_dir, f'report_{report_id}.csv')

            # Get the current timestamp (max timestamp in the data)
            current_timestamp = db.session.query(func.max(StoreStatus.timestamp_utc)).scalar()

            # Get all store IDs
            store_ids = db.session.query(distinct(StoreStatus.store_id)).all()
            store_ids = [store_id[0] for store_id in store_ids]

            # Create a DataFrame to store the results
            results = []

            # Process each store
            for store_id in store_ids:
                # Calculate metrics for this store
                metrics = calculate_store_metrics(store_id, current_timestamp)
                results.append(metrics)

            # Create a DataFrame from the results
            df = pd.DataFrame(results)

            # Save the report to a CSV file
            df.to_csv(output_file, index=False)

            # Update the report status in the database
            report = Report.query.filter_by(report_id=report_id).first()
            report.status = 'Complete'
            report.completed_at = datetime.utcnow()
            report.file_path = output_file
            db.session.commit()

        except Exception as e:
            print(f"Error generating report: {e}")
            # Update the report status to indicate failure
            report = Report.query.filter_by(report_id=report_id).first()
            report.status = 'Failed'
            db.session.commit()

def calculate_store_metrics(store_id, current_timestamp):
    """
    Calculate uptime and downtime metrics for a specific store
    """
    # Get the store's timezone
    timezone_record = StoreTimezone.query.filter_by(store_id=store_id).first()
    timezone_str = timezone_record.timezone_str if timezone_record else 'America/Chicago'
    timezone = pytz.timezone(timezone_str)

    # Define the time periods
    last_hour = current_timestamp - timedelta(hours=1)
    last_day = current_timestamp - timedelta(days=1)
    last_week = current_timestamp - timedelta(weeks=1)

    # Get the store's business hours
    business_hours = BusinessHours.query.filter_by(store_id=store_id).all()

    # If no business hours are defined, assume 24/7
    is_24x7 = len(business_hours) == 0

    # Get the store's status observations
    status_records = StoreStatus.query.filter_by(store_id=store_id).filter(
        StoreStatus.timestamp_utc >= last_week
    ).order_by(StoreStatus.timestamp_utc).all()

    # Calculate metrics for each time period
    uptime_last_hour, downtime_last_hour = calculate_uptime_downtime(
        status_records, last_hour, current_timestamp, business_hours, timezone, is_24x7
    )

    uptime_last_day, downtime_last_day = calculate_uptime_downtime(
        status_records, last_day, current_timestamp, business_hours, timezone, is_24x7
    )

    uptime_last_week, downtime_last_week = calculate_uptime_downtime(
        status_records, last_week, current_timestamp, business_hours, timezone, is_24x7
    )

    # Return the metrics
    return {
        'store_id': store_id,
        'uptime_last_hour': round(uptime_last_hour / 60, 2),  # Convert to minutes
        'uptime_last_day': round(uptime_last_day / 3600, 2),  # Convert to hours
        'uptime_last_week': round(uptime_last_week / 3600, 2),  # Convert to hours
        'downtime_last_hour': round(downtime_last_hour / 60, 2),  # Convert to minutes
        'downtime_last_day': round(downtime_last_day / 3600, 2),  # Convert to hours
        'downtime_last_week': round(downtime_last_week / 3600, 2)  # Convert to hours
    }

def calculate_uptime_downtime(status_records, start_time, end_time, business_hours, timezone, is_24x7):
    """
    Calculate uptime and downtime for a specific time period

    This function calculates uptime and downtime for a store during a specific time period,
    taking into account the store's business hours. It extrapolates uptime and downtime
    based on the periodic polls we have ingested.
    """
    # Filter status records for the time period
    period_records = [r for r in status_records if start_time <= r.timestamp_utc <= end_time]

    # Initialize uptime and downtime counters
    uptime_seconds = 0
    downtime_seconds = 0

    # If the store is open 24/7, we can simplify the calculation
    if is_24x7:
        # Calculate the total time in the period
        total_seconds = (end_time - start_time).total_seconds()

        if not period_records:
            # No data for this period, assume store was inactive
            return 0, total_seconds

        # Calculate the percentage of active observations
        active_count = sum(1 for r in period_records if r.status == 'active')
        if len(period_records) > 0:
            active_ratio = active_count / len(period_records)
            uptime_seconds = total_seconds * active_ratio
            downtime_seconds = total_seconds * (1 - active_ratio)
    else:
        # We need to check each interval against business hours
        # Group observations by day
        days = {}
        current_day = start_time
        while current_day <= end_time:
            days[current_day.date()] = []
            current_day += timedelta(days=1)

        for record in period_records:
            days[record.timestamp_utc.date()].append(record)

        # Process each day
        for day_date, day_records in days.items():
            # Get the day of week (0=Monday, 6=Sunday)
            day_of_week = day_date.weekday()

            # Get business hours for this day
            day_hours = [h for h in business_hours if h.day_of_week == day_of_week]

            # If no business hours defined for this day, skip
            if not day_hours:
                continue

            # Process each business hour interval
            for hour_interval in day_hours:
                # Convert business hours to UTC for comparison
                local_date = day_date
                local_start = datetime.combine(local_date, hour_interval.start_time_local)
                local_end = datetime.combine(local_date, hour_interval.end_time_local)

                # Handle case where end time is on the next day
                if hour_interval.end_time_local < hour_interval.start_time_local:
                    local_end = local_end + timedelta(days=1)

                # Convert to UTC
                local_tz = timezone
                local_start = local_tz.localize(local_start)
                local_end = local_tz.localize(local_end)
                utc_start = local_start.astimezone(pytz.UTC).replace(tzinfo=None)
                utc_end = local_end.astimezone(pytz.UTC).replace(tzinfo=None)

                # Adjust to the time period we're calculating for
                if utc_start < start_time:
                    utc_start = start_time
                if utc_end > end_time:
                    utc_end = end_time

                # Skip if the interval is outside our time period
                if utc_end <= utc_start:
                    continue

                # Get observations during this business hour interval
                interval_records = [r for r in day_records if utc_start <= r.timestamp_utc <= utc_end]

                # Calculate uptime/downtime for this interval
                interval_seconds = (utc_end - utc_start).total_seconds()

                if interval_records:
                    # Calculate based on the ratio of active observations
                    active_count = sum(1 for r in interval_records if r.status == 'active')
                    active_ratio = active_count / len(interval_records)

                    uptime_seconds += interval_seconds * active_ratio
                    downtime_seconds += interval_seconds * (1 - active_ratio)
                else:
                    # No observations during this business hour interval
                    # Assume the store was inactive (downtime)
                    downtime_seconds += interval_seconds

    return uptime_seconds, downtime_seconds
