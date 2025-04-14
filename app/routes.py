from flask import Blueprint, current_app, json, jsonify, render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_login import login_user, login_required, current_user

from app.services.recommendations import generate_recommendations
from .models import db, Recommendation, User, MoodSurvey
from .forms import MoodSurveyForm, LoginForm, SignupForm
from datetime import date, timedelta
from datetime import datetime
from flask_limiter.util import get_remote_address
import openai  # Add this with your other imports

#nuk osht ka i analizon mir tdhanat e survey , edhe po i jep tnjejtat rekomandime gjith mdoket, edhe po i printon keq vlerat qe pja jepi

# Create a blueprint for the routes
main = Blueprint('main', __name__)

# Home route
@main.route('/')
def home():
    return render_template('index.html')


# Initialize Limiter with app context
def init_limiter(app):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["500 per day", "3 per second"]
    )
    return limiter

limiter = Limiter(key_func=get_remote_address)

@main.route('/recommend', methods=['POST'])
@limiter.limit("3 per minute") 
def recommend():
    data = request.get_json()
    recommendations = generate_recommendations(data)
    return jsonify(recommendations)

# Login route
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            
            # Check for surveys in last 24 hours
            twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
            recent_survey = MoodSurvey.query.filter(
                MoodSurvey.user_id == user.user_id,
                MoodSurvey.survey_date >= twenty_four_hours_ago
            ).first()
            
            if recent_survey:
                return redirect(url_for('main.mainpage'))
            else:
                return redirect(url_for('main.survey'))
        
        flash("Invalid credentials", "error")
        
    return render_template('login.html', form=form)


@main.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    form = MoodSurveyForm()
    
    if form.validate_on_submit():
        try:
            # Start transaction
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
            db.session.flush()  # Assigns ID without committing

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
                recommendation_text=json.dumps(recommendations),
                created_at=datetime.utcnow()
            )
            db.session.add(rec)
            
            # Commit transaction
            db.session.commit()
            
            # Store in session for immediate display
            session['latest_recommendations'] = recommendations
            session.modified = True
            
            return redirect(url_for('main.survey_complete'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Survey submission error: {str(e)}")
            flash("Error processing your survey. Please try again.", "error")
    
    return render_template('survey.html', form=form)

@main.route('/survey_complete')
@login_required
def survey_complete():
    # Try to get from session first
    recommendations = session.get('latest_recommendations')
    source = 'ai'
    
    # If not in session, get from database
    if not recommendations:
        latest_survey = MoodSurvey.query.filter_by(
            user_id=current_user.user_id
        ).order_by(MoodSurvey.survey_date.desc()).first()
        
        if latest_survey:
            rec = Recommendation.query.filter_by(
                survey_id=latest_survey.survey_id
            ).first()
            
            if rec:
                recommendations = rec.recommendation_text.split('\n')
                source = 'database'
    
    # Fallback recommendations
    if not recommendations:
        recommendations = [
            "Take three deep breaths to center yourself",
            "Drink a glass of water",
            "Step outside for fresh air"
        ]
        source = 'fallback'
        flash("We're preparing your personalized recommendations. Here are some general wellness tips.", "info")
    
    # Format recommendations for display
    formatted_recs = []
    for rec in recommendations:
        if '•' in rec:
            parts = rec.split('•')[1].split('(')
            formatted_recs.append({
                'category': parts[0].split(']')[0].strip(' ['),
                'text': parts[0].split(']')[1].strip(),
                'rationale': parts[1].strip(')') if len(parts) > 1 else ''
            })
        else:
            formatted_recs.append({
                'category': 'General',
                'text': rec,
                'rationale': ''
            })
    
    return render_template('survey_complete.html',
                        recommendations=formatted_recs,
                        source=source)


@main.route('/healthcheck')
def health_check():
    """Endpoint to verify database connectivity"""
    try:
        # Simple query to verify database connection
        db.session.execute("SELECT 1")
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': str(e)}), 500

@main.route('/mainpage')
@login_required
def mainpage():
    return render_template('mainpage.html')  # Make sure this template exists

def build_ai_prompt(analysis, survey_data):
    """Builds a prompt that definitely includes all survey factors"""
    # Safely get all values with defaults
    factors = {
        'Mood': str(survey_data.get('mood_level', '?')) + '/10',
        'Stress': str(survey_data.get('stress_level', '?')) + '/10',
        'Energy': str(survey_data.get('energy_level', '?')) + '/10',
        'Sleep': str(survey_data.get('sleep_hours', '?')) + ' hours',
        'Diet': str(survey_data.get('diet_quality', '?')) + '/10',
        'Activity': str(survey_data.get('physical_activity', '?')) + '/10',
        'Social Contact': 'Yes' if survey_data.get('spent_time_with_someone') == 'yes' else 'No',
        'Current Feelings': f'"{survey_data.get("feelings_description", "not specified")}"'
    }

    # Build the factors table for clear visualization
    factors_table = "\n".join([f"- {k}: {v}" for k, v in factors.items()])

    prompt = f"""
    **Complete Mental Health Assessment**

    User's Current State:
    {factors_table}

    Analysis Insights:
    - Primary Concern: {analysis.get('key_concerns', ['none'])[0]}
    - Mood Pattern: {analysis.get('mood_profile', 'unknown')}
    - Stress Level: {analysis.get('stress_profile', 'unknown')}
    - Energy State: {analysis.get('energy_analysis', 'unknown')}
    - Lifestyle Factors: {', '.join(analysis.get('lifestyle_factors', [])) or 'none'}

    Recommendation Requirements:
    1. Must address ALL these factors: {list(factors.keys())}
    2. Give specific actions (no generic advice)
    3. Include one social interaction suggestion if isolated
    4. Add one nutrition tip if diet score <6
    5. Include energy management if energy <5

    Expected Format:
    [Domain] Specific Recommendation (Scientific Rationale)
    """
    return prompt

# Signup route
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data  # This creates a tuple instead of a string

        email = form.email.data
        password = form.password.data
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email already in use.", "error")
            return redirect(url_for('main.signup'))
        
        # Create a new user
        new_user = User(name=name, email=email)  # Make sure username is included here
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('main.login'))
    
    return render_template('signup.html', form=form)