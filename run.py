from app import create_app, db
from app.models.models import StoreStatus, BusinessHours, StoreTimezone, Report
from app.utils.data_importer import import_data
import os
from flask import Flask

app = create_app()

# Initialize database function
def initialize_database():
    # Create the database tables
    db.create_all()

    # Check if data needs to be imported
    if StoreStatus.query.count() == 0:
        import_data()

# Register a function to run before the first request (using modern approach)
@app.route('/init-db')
def init_db_route():
    initialize_database()
    return "Database initialized"

if __name__ == '__main__':
    # Create the database file if it doesn't exist
    with app.app_context():
        if not os.path.exists(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app', 'store_monitoring.db')):
            db.create_all()
            import_data()

    # Run the application
    app.run(debug=True, host='0.0.0.0', port=8080)
