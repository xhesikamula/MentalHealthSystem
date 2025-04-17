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
        

