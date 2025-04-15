from flask import Flask, current_app, json, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from flask_migrate import Migrate
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, create_app
from app.models import User, MoodSurvey, JournalEntry, Recommendation, Notification, Event
from app.forms import SignupForm, MoodSurveyForm
from dotenv import load_dotenv
import os

from app.services.recommendations import generate_recommendations

# Load environment variables FIRST
load_dotenv()

# Initialize the Flask app
app = create_app()
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database and migration setup
migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('survey'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('survey'))
        
        flash("Invalid email or password", "error")
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('survey'))

    form = SignupForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already in use", "error")
            return redirect(url_for('signup'))

        user = User(
            name=form.name.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='user'  # Default role for new users
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

@app.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    form = MoodSurveyForm()
    
    # Check for existing survey today
    today = date.today()
    existing_survey = MoodSurvey.query.filter(
        MoodSurvey.user_id == current_user.user_id,
        db.func.date(MoodSurvey.survey_date) == today
    ).first()
    
    if existing_survey:
        flash("You've already completed today's survey", "info")
        return redirect(url_for('survey_complete'))

    if form.validate_on_submit():
        try:
            # Create survey entry
            survey = MoodSurvey(
                user_id=current_user.user_id,
                mood_level=form.mood_level.data,
                stress_level=form.stress_level.data,
                sleep_hours=form.sleep_hours.data,
                energy_level=form.energy_level.data,
                diet_quality=form.diet_quality.data,
                physical_activity=form.physical_activity.data,
                spent_time_with_someone=form.spent_time_with_someone.data,
                feelings_description=form.feelings_description.data,
                survey_date=datetime.utcnow()
            )
            db.session.add(survey)
            db.session.commit()

            # Generate recommendations
            recommendations = generate_recommendations({
                'mood_level': survey.mood_level,
                'stress_level': survey.stress_level,
                'sleep_hours': survey.sleep_hours,
                'energy_level': survey.energy_level,
                'diet_quality': survey.diet_quality,
                'physical_activity': survey.physical_activity,
                'spent_time_with_someone': survey.spent_time_with_someone,
                'feelings_description': survey.feelings_description
            })

            # Save recommendations
            rec = Recommendation(
                survey_id=survey.survey_id,
                recommendation_text="\n".join(recommendations)
            )
            db.session.add(rec)
            db.session.commit()

            # Store in session for immediate display
            session['latest_recommendations'] = recommendations
            
            # Clear form data
            form.process()
            
            return redirect(url_for('survey_complete'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Survey error: {str(e)}")
            flash("Error processing your survey. Please try again.", "error")
    
    return render_template('survey.html', form=form)

@app.route('/survey_complete')
@login_required
def survey_complete():
    # Try to get from session first
    recommendations = session.get('latest_recommendations')
    
    # If not in session, check database
    if not recommendations:
        latest_survey = MoodSurvey.query.filter_by(
            user_id=current_user.user_id
        ).order_by(MoodSurvey.survey_date.desc()).first()
        
        if latest_survey:
            rec = Recommendation.query.filter_by(
                survey_id=latest_survey.survey_id
            ).first()
            if rec:
                try:
                    # Try to parse as JSON if stored that way
                    recommendations = json.loads(rec.recommendation_text)
                except:
                    # Fallback to string split
                    recommendations = [r.strip() for r in rec.recommendation_text.split('\n') if r.strip()]
    
    # Format recommendations consistently
    formatted_recs = []
    if recommendations:
        if isinstance(recommendations, str):
            formatted_recs = [{'category': 'General', 'text': recommendations}]
        else:
            for rec in recommendations if isinstance(recommendations, list) else [recommendations]:
                if isinstance(rec, str):
                    formatted_recs.append({'category': 'General', 'text': rec})
                elif isinstance(rec, dict):
                    formatted_recs.append({
                        'category': rec.get('category', 'General'),
                        'text': rec.get('text', ''),
                        'rationale': rec.get('rationale', '')
                    })
    
    return render_template('survey_complete.html',
                        recommendations=formatted_recs or None)


@app.route('/journal', methods=['GET', 'POST'])
@login_required
def journal():
    if request.method == 'POST':
        content = request.form.get('content')
        if content:
            entry = JournalEntry(
                user_id=current_user.user_id,
                content=content
            )
            db.session.add(entry)
            db.session.commit()
            flash("Journal entry saved successfully", "success")
            return redirect(url_for('journal'))
    
    entries = JournalEntry.query.filter_by(user_id=current_user.user_id).order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal.html', entries=entries)

if __name__ == '__main__':
    app.run(debug=True)