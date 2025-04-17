# app/db_operations.py
from .models import db

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
