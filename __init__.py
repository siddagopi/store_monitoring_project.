from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configure the SQLite database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'store_monitoring.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the database with the app
    db.init_app(app)

    # Import and register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/')

    return app
