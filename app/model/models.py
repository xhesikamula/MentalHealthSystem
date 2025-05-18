from datetime import datetime, date
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy

#eshte bo set up databaza
db = SQLAlchemy()

class Event(db.Model):
    __tablename__ = 'events'
    
    event_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    description = db.Column(db.Text)
    date_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    source = db.Column(db.String(100))
    type = db.Column(db.Enum('event', 'hotline', 'article', 'podcast', 'video'), nullable=False, default='event')
    link = db.Column(db.String(255))
    phone_number = db.Column(db.String(20))  # Added phone number field
    image_url = db.Column(db.String(255)) # also added this one
    users = db.relationship('User', secondary='userevents', backref='events', lazy='dynamic')

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    preferences = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    # role = db.Column(db.Enum('admin', 'user'), nullable=False, default='user')
    role = db.Column(db.Enum('admin', 'user', name='role_enum'), nullable=False, default='user')
    image_url = db.Column(db.String(255))  

    # Relationships
    mood_surveys = db.relationship('MoodSurvey', back_populates='user', lazy='dynamic')
    journal_entries = db.relationship('JournalEntry', back_populates='user', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='user', lazy='dynamic')

    def get_id(self):
        return str(self.user_id)  
    
    #i bona koment se i kom te db_operations.py tash stored procedures
    # def set_password(self, password):
    #     self.password_hash = generate_password_hash(password)
    
    # def check_password(self, password):
    #     return check_password_hash(self.password_hash, password)
    
    # def update_profile(self, name, email, preferences):
    #     """Helper method to update profile"""
    #     self.name = name
    #     self.email = email
    #     self.preferences = preferences
    #     db.session.commit()

class MoodSurvey(db.Model):
    __tablename__ = 'moodsurvey'
    
    survey_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    mood_level = db.Column(db.Integer)
    stress_level = db.Column(db.Integer)
    sleep_hours = db.Column(db.Float)
    energy_level = db.Column(db.Integer)
    diet_quality = db.Column(db.Integer)
    physical_activity = db.Column(db.Integer, default=0)
    spent_time_with_someone = db.Column(db.Enum('yes', 'no'), nullable=False)
    feelings_description = db.Column(db.Text)
    survey_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', back_populates='mood_surveys')
    recommendation = db.relationship(
        'Recommendation', 
        uselist=False, #one survey has only ONE recommendation
        back_populates='mood_survey', 
        cascade='all, delete-orphan' #if a MoodSurvey gets deleted, automatically delete the linked Recommendation too
    )

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    
    rec_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recommendation_text = db.Column(db.Text, nullable=False)
    survey_id = db.Column(db.Integer, db.ForeignKey('moodsurvey.survey_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    mood_survey = db.relationship('MoodSurvey', back_populates='recommendation')

class JournalEntry(db.Model):
    __tablename__ = 'journalentry'
    
    entry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', back_populates='journal_entries')
    sentiment_analyses = db.relationship('SentimentAnalysis', back_populates='journal_entry', lazy='dynamic')

class SentimentAnalysis(db.Model):
    __tablename__ = 'sentimentanalysis'
    
    analysis_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('journalentry.entry_id'))
    sentiment_type = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship
    journal_entry = db.relationship('JournalEntry', back_populates='sentiment_analyses')

# #edhe qita
# class Notification(db.Model):
#     __tablename__ = 'notifications'
    
#     notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
#     message = db.Column(db.Text, nullable=False)
#     sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
#     status = db.Column(db.Enum('sent', 'pending'), default='pending')
#     type = db.Column(db.Enum('survey', 'journal', 'mindfulness'), default='survey')
    
#     # Relationship
#     user = db.relationship('User', back_populates='notifications')

class UserEvents(db.Model):
    __tablename__ = 'userevents'
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), primary_key=True)



#tshtunen
# class Notification(db.Model):
#     __tablename__ = 'notifications'
    
#     notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
#     message = db.Column(db.Text, nullable=False)
#     sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
#     status = db.Column(db.Enum('sent', 'pending'), default='pending')
#     type = db.Column(db.Enum('survey', 'journal', 'mindfulness'), default='survey')
    
#     # Relationship
#     user = db.relationship('User', back_populates='notifications')

#i shtova
#models/notification.py
class Notification(db.Model):
    __tablename__ = 'notifications'

    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))
    message = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    link = db.Column(db.String(255))  # e.g. '/survey'
    type = db.Column(db.Enum('survey', 'journal', 'mindfulness'), default='survey')
    status = db.Column(db.Enum('sent', 'pending'), default='pending')

    user = db.relationship('User', back_populates='notifications')