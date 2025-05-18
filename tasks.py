from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app
from app.model.models import User
from app.dal.db_operations import DBOperations
from datetime import date

def check_surveys_and_notify():
    with current_app.app_context():
        users = User.query.all()
        for user in users:
            has_survey_today = DBOperations.has_survey_today(user.user_id, date.today())
            if not has_survey_today:
                DBOperations.create_notification(
                    user_id=user.user_id,
                    message="You have not completed your daily mental health survey. Please take a moment to check in.",
                    type_="survey"
                )

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_surveys_and_notify, trigger='interval', minutes=15)
    scheduler.start()

    # Shut down scheduler when app exits
    import atexit
    atexit.register(lambda: scheduler.shutdown())