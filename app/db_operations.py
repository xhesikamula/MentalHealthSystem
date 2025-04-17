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
from flask import current_app
from .models import db
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
        
#so tu bo
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
        db.session.execute(
            text("CALL CreateMoodSurvey(:user_id, :mood_level, :stress_level, "
                ":sleep_hours, :energy_level, :diet_quality, "
                ":physical_activity, :spent_time, :feelings, :recommendation, @survey_id)"),
            {
                'user_id': user_id,
                'mood_level': mood_level,
                'stress_level': stress_level,
                'sleep_hours': sleep_hours,
                'energy_level': energy_level,
                'diet_quality': diet_quality,
                'physical_activity': physical_activity,
                'spent_time': spent_time_with_someone,
                'feelings': feelings_description,
                'recommendation': recommendation_text
            }
        )

        # Get the OUT parameter
        survey_id = db.session.execute(text("SELECT @survey_id")).scalar()
        db.session.commit()
        
        if survey_id:
            current_app.logger.info(f"Successfully created survey {survey_id}")
            return survey_id
        return None

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create survey: {str(e)}", exc_info=True)
        return None
    
# @staticmethod
# def get_user_survey_history(user_id, limit=10):
#     """
#     Calls the GetUserSurveyHistory stored procedure
#     """
#     try:
#         result = db.session.execute(
#             text("CALL GetUserSurveyHistory(:p_user_id, :p_limit)"),
#             {
#                 'p_user_id': user_id,
#                 'p_limit': limit
#             }
#         )
#         # Get the result set
#         surveys = result.fetchall()
#         return surveys
#     except Exception as e:
#         current_app.logger.error(f"Failed to get survey history: {str(e)}")
#         return []