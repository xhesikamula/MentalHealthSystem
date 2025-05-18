# app/db_operations.py
from datetime import date, datetime
from flask import current_app
from app.model.models import JournalEntry, SentimentAnalysis, MoodSurvey, User, Event, db
from sqlalchemy import text

class DBOperations:
    @staticmethod
    def CreateUser(name, email, password_hash):
        try:
            result = db.session.execute(
                "CALL CreateUser(:name, :email, :password_hash)",
                {'name': name, 'email': email, 'password_hash': password_hash}
            )
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print("DB Error (CreateUser):", e)
            return False

    @staticmethod
    def change_password(user_id, new_password_hash):
        try:
            result = db.session.execute(
                text("CALL ChangePassword(:p_user_id, :p_new_password_hash)"),
                {
                    'p_user_id': user_id,
                    'p_new_password_hash': new_password_hash
                }
            )
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Password change failed: {str(e)}")
            return False

    @staticmethod
    def update_user_profile(user_id, name, email, preferences):
        try:
            result = db.session.execute(
                text("CALL UpdateUserProfile(:p_user_id, :p_name, :p_email, :p_preferences)"),
                {
                    'p_user_id': user_id,
                    'p_name': name,
                    'p_email': email,
                    'p_preferences': preferences
                }
            )
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Profile update failed: {str(e)}")
            return False

    @staticmethod
    def create_mood_survey(user_id, mood_level, stress_level, sleep_hours,
                           energy_level, diet_quality, physical_activity,
                           spent_time_with_someone, feelings_description, recommendation_text):
        try:
            db.session.execute(text("SELECT 1")).fetchone()

            db.session.execute(
                text("CALL CreateMoodSurvey(:p_user_id, :p_mood_level, :p_stress_level, "
                     ":p_sleep_hours, :p_energy_level, :p_diet_quality, "
                     ":p_physical_activity, :p_spent_time_with_someone, :p_feelings_description, "
                     ":p_recommendation_text, @p_survey_id)"),
                {
                    'p_user_id': user_id,
                    'p_mood_level': mood_level,
                    'p_stress_level': stress_level,
                    'p_sleep_hours': sleep_hours,
                    'p_energy_level': energy_level,
                    'p_diet_quality': diet_quality,
                    'p_physical_activity': physical_activity,
                    'p_spent_time_with_someone': spent_time_with_someone,
                    'p_feelings_description': feelings_description,
                    'p_recommendation_text': recommendation_text
                }
            )
            survey_id = db.session.execute(text("SELECT @p_survey_id")).scalar()
            db.session.commit()

            if survey_id:
                current_app.logger.info(f"Successfully created survey {survey_id}")
                return survey_id
            return None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create survey: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_user_survey_history(user_id, limit=10):
        try:
            result = db.session.execute(
                text("CALL GetUserSurveyHistory(:user_id, :limit)"),
                {'user_id': user_id, 'limit': limit}
            )
            return [dict(row) for row in result]
        except Exception as e:
            current_app.logger.error(f"Error getting history: {str(e)}")
            return None

    @staticmethod
    def create_journal_entry(user_id, content, sentiment_type, confidence_score):
        try:
            db.session.execute(text("SELECT 1")).fetchone()

            db.session.execute(
                text("CALL CreateJournalEntry(:p_user_id, :p_content, :p_sentiment_type, :p_confidence_score, @p_entry_id)"),
                {
                    'p_user_id': user_id,
                    'p_content': content,
                    'p_sentiment_type': sentiment_type,
                    'p_confidence_score': confidence_score
                }
            )
            entry_id = db.session.execute(text("SELECT @p_entry_id")).scalar()
            db.session.commit()

            if entry_id:
                current_app.logger.info(f"Created journal entry with ID: {entry_id}")
                return entry_id
            return None
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create journal entry: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def get_journal_entries_with_sentiment(user_id, start_date=None, end_date=None):
        try:
            if not start_date:
                start_date = datetime(2023, 1, 1).date()
            if not end_date:
                end_date = datetime.today().date()

            result = db.session.execute(
                text("CALL GetJournalEntries(:user_id, :start_date, :end_date)"),
                {
                    'user_id': user_id,
                    'start_date': start_date,
                    'end_date': end_date
                }
            )
            entries = []
            for row in result:
                entry = dict(row)
                if 'created_at' in entry and entry['created_at']:
                    if isinstance(entry['created_at'], str):
                        entry['created_at'] = datetime.fromisoformat(entry['created_at'])
                entries.append(entry)

            return entries
        except Exception as e:
            current_app.logger.error(f"Error getting journal entries: {str(e)}")
            return None

    @staticmethod
    def create_notification(user_id, message, type_):
        try:
            current_app.logger.info(f"Calling CreateNotification with user_id={user_id}, message={message}, type={type_}")

            db.session.execute(
                text("CALL CreateNotification(:p_user_id, :p_message, :p_type_)"),
                {'p_user_id': user_id, 'p_message': message, 'p_type_': type_}
            )

            db.session.commit()
            current_app.logger.info("Notification created successfully.")
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"DB Error (CreateNotification): {e}")
            return False

    @staticmethod
    def get_pending_notifications(user_id):
        try:
            result = db.session.execute(
                text("CALL GetPendingNotifications(:p_user_id)"),
                {'p_user_id': user_id}
            )
            notifications = [dict(row) for row in result]
            return notifications
        except Exception as e:
            print("DB Error (GetPendingNotifications):", e)
            return []

    @staticmethod
    def mark_notifications_sent(notification_ids):
        try:
            db.session.execute(
                text("CALL MarkNotificationsSent(:p_notification_ids)"),
                {'p_notification_ids': notification_ids}
            )
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print("DB Error (MarkNotificationsSent):", e)
            return False

    @staticmethod
    def has_survey_today(user_id, check_date=None):
        if check_date is None:
            check_date = date.today()
        return db.session.query(MoodSurvey).filter_by(user_id=user_id, survey_date=check_date).count() > 0

    @staticmethod
    def check_survey_and_notify(user_id):
        try:
            current_app.logger.info(f"Calling CheckSurveyAndNotify with user_id={user_id}")
            db.session.execute(
                text("CALL CheckSurveyAndNotify(:p_user_id)"),
                {'p_user_id': user_id}
            )
            db.session.commit()
            current_app.logger.info("CheckSurveyAndNotify executed successfully.")
            return True
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"DB Error (CheckSurveyAndNotify): {e}")
            return False


# --- ADMIN FUNCTIONS ---

def get_all_users():
    return User.query.all()

def delete_user_and_surveys(user_id):
    try:
        MoodSurvey.query.filter_by(user_id=user_id).delete()
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return str(e)

def get_recent_events(limit=5):
    return Event.query.order_by(Event.date_time.desc()).limit(limit).all()

def get_events_by_type(event_type):
    return Event.query.filter(Event.type == event_type).all()

def delete_event_by_id(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()

def add_new_event(event):
    db.session.add(event)
    db.session.commit()

def get_recent_surveys(limit=5):
    return MoodSurvey.query.order_by(MoodSurvey.created_at.desc()).limit(limit).all()
