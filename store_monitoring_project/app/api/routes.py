from flask import Blueprint, jsonify, request, send_file
from app.models.models import Report
from app import db
from app.utils.report_generator import generate_report
import uuid
import os
import threading

api_bp = Blueprint('api', __name__)

@api_bp.route('/trigger_report', methods=['POST'])
def trigger_report():
    """
    Endpoint to trigger report generation from the data provided (stored in DB)
    No input
    Output - report_id (random string)
    """
    # Generate a unique report ID
    report_id = str(uuid.uuid4())

    # Create a new report record in the database
    new_report = Report(report_id=report_id, status='Running')
    db.session.add(new_report)
    db.session.commit()

    # Start report generation in a background thread
    thread = threading.Thread(target=generate_report, args=(report_id,))
    thread.daemon = True
    thread.start()

    return jsonify({'report_id': report_id})

@api_bp.route('/get_report', methods=['GET'])
def get_report():
    """
    Endpoint to check the status of a report or download the completed report
    Input - report_id
    Output:
    - if report generation is not complete, return "Running" as the output
    - if report generation is complete, return "Complete" along with the CSV file
    """
    report_id = request.args.get('report_id')

    if not report_id:
        return jsonify({'error': 'report_id is required'}), 400

    # Find the report in the database
    report = Report.query.filter_by(report_id=report_id).first()

    if not report:
        return jsonify({'error': 'Report not found'}), 404

    # If the report is still running, return the status
    if report.status == 'Running':
        return jsonify({'status': 'Running'})

    # If the report is complete, return the CSV file
    if report.status == 'Complete' and report.file_path:
        return send_file(report.file_path,
                         mimetype='text/csv',
                         as_attachment=True,
                         download_name=f'report_{report_id}.csv')

    # If something went wrong with the report
    return jsonify({'error': 'Report generation failed'}), 500
