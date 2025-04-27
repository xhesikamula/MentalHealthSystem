# # app/db_operations.py
# from .models import db

# class DBOperations:
#     @staticmethod
#     def CreateUser(name, email, password_hash):
#         try:
#             # Use raw SQL to call the stored procedure
#             result = db.session.execute(
#                 "CALL CreateUser(:name, :email, :password_hash)",
#                 {'name': name, 'email': email, 'password_hash': password_hash}
#             )
#             db.session.commit()
#             return True
#         except Exception as e:
#             db.session.rollback()
#             print("DB Error (CreateUser):", e)
#             return False


# app/db_operations.py
from datetime import datetime
from flask import current_app
from .models import JournalEntry, SentimentAnalysis, db
from sqlalchemy import text

class DBOperations:
    @staticmethod
    def CreateUser(name, email, password_hash):
        try:
            # Use raw SQL to call the stored procedure
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
        """
        Calls the ChangePassword stored procedure to update the user's password.
        Args:
            user_id: ID of the user whose password needs to be changed
            new_password_hash: New password hash
        Returns:
            bool: True if successful, False if failed
        """
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
        """
        Calls the UpdateUserProfile stored procedure
        Args:
            user_id: ID of the user to update
            name: New name for the user
            email: New email for the user
            preferences: New preferences
        Returns:
            bool: True if successful, False if failed
        """
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
        """
        Calls the CreateMoodSurvey stored procedure to save a mood survey
        """
        try:
            # Verify database connection
            db.session.execute(text("SELECT 1")).fetchone()

            # Call stored procedure
            result = db.session.execute(
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

            # Get the OUT parameter
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
    """Using your existing procedure"""
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
        """
        Calls the CreateJournalEntry stored procedure to save a journal entry and its sentiment.
        Returns:
            The created entry_id if successful, None otherwise.
        """
        try:
            db.session.execute(text("SELECT 1")).fetchone()  # Ensure DB connection is alive

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
        

# @staticmethod
# def get_journal_entries_with_sentiment(user_id, start_date, end_date):
#     try:
#         # Execute the stored procedure
#         result = db.session.execute(
#             text("CALL GetJournalEntries(:user_id, :start_date, :end_date)"),
#             {'user_id': user_id, 'start_date': start_date, 'end_date': end_date}
#         )
#         # Return the result as a list of dictionaries
#         return [dict(row) for row in result]
#     except Exception as e:
#         print(f"Error executing stored procedure: {e}")
#         return None

#nuk mka bo
# @staticmethod
# def get_journal_entries_with_sentiment(user_id, start_date=None, end_date=None):
#         """Get journal entries with sentiment analysis using the stored procedure"""
#         try:
#             # Set default dates if not provided
#             if not start_date:
#                 start_date = datetime(2023, 1, 1).date()
#             if not end_date:
#                 end_date = datetime.today().date()
            
#             # Call the stored procedure
#             result = db.session.execute(
#                 text("CALL GetJournalEntries(:user_id, :start_date, :end_date)"),
#                 {
#                     'user_id': user_id,
#                     'start_date': start_date,
#                     'end_date': end_date
#                 }
#             )
            
#             # Convert to list of dictionaries
#             entries = []
#             for row in result:
#                 entry = dict(row)
#                 # Ensure datetime is properly formatted
#                 if 'created_at' in entry and entry['created_at']:
#                     if isinstance(entry['created_at'], str):
#                         entry['created_at'] = datetime.fromisoformat(entry['created_at'])
#                 entries.append(entry)
            
#             return entries
            
#         except Exception as e:
#             current_app.logger.error(f"Error getting journal entries: {str(e)}")
#             return None