from app import db
from datetime import datetime

class StoreStatus(db.Model):
    __tablename__ = 'store_status'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    timestamp_utc = db.Column(db.DateTime, nullable=False)
    
    def __repr__(self):
        return f'<StoreStatus {self.store_id} {self.status} {self.timestamp_utc}>'

class BusinessHours(db.Model):
    __tablename__ = 'business_hours'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(100), nullable=False, index=True)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time_local = db.Column(db.Time, nullable=False)
    end_time_local = db.Column(db.Time, nullable=False)
    
    def __repr__(self):
        return f'<BusinessHours {self.store_id} Day:{self.day_of_week} {self.start_time_local}-{self.end_time_local}>'

class StoreTimezone(db.Model):
    __tablename__ = 'store_timezone'
    
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    timezone_str = db.Column(db.String(100), nullable=False)
    
    def __repr__(self):
        return f'<StoreTimezone {self.store_id} {self.timezone_str}>'

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='Running')  # Running or Complete
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Report {self.report_id} {self.status}>'
