# app/controllers/services/notification_service.py
from app.model.models import Notification
from app import db

def notify_once(user_id, message, link):
    existing = Notification.query.filter_by(user_id=user_id, message=message, link=link).first()
    if not existing:
        notif = Notification(user_id=user_id, message=message, link=link)
        db.session.add(notif)
        db.session.commit()
