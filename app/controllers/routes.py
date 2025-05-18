from asyncio import Event
from wsgiref import headers
import requests
from sqlalchemy import text
from flask import Blueprint, current_app, json, jsonify, render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_login import login_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy  
from langdetect import detect as detect_language


from ..model.models import Notification, db, Recommendation, User, MoodSurvey
from ..forms import ChangePasswordForm, MoodSurveyForm, LoginForm, SignupForm
from datetime import date, timedelta, datetime
from flask_limiter.util import get_remote_address
import openai  
from app.dal.db_operations import DBOperations
from app.model.models import JournalEntry
import json
from ..dal import db_operations 
from app.controllers.services.recommendations import get_llama_recommendation
from app.controllers.services.recommendations import translate_to_english

#per api
from dotenv import load_dotenv
import os
from app.forms import JournalEntryForm
import app as app


load_dotenv()  # Load environment variables from .env file

API_KEY = os.getenv('GEOAPIFY_API_KEY')  

#nuk osht ka i analizon mir tdhanat e survey , edhe po i jep tnjejtat rekomandime gjith mdoket, edhe po i printon keq vlerat qe pja jepi

#This groups our user-related routes 
main = Blueprint('main', __name__)

# Home route
@main.route('/')
def home():
    return render_template('index.html')

#we created a limiter so users don't spam the server
def init_limiter(app):
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["500 per day", "3 per second"]
    )
    return limiter

limiter = Limiter(key_func=get_remote_address)

from app.model.models import Event

@main.route('/events/list')
@login_required
def list_events():
    #I bon fetch veq eventet te tipit event
    events = Event.query.filter_by(type='event').all()
    return render_template('events_list.html', events=events)

@main.route('/podcasts')
@login_required
def podcasts():
    podcasts = Event.query.filter(Event.type == 'podcast').all()
    return render_template('podcasts_list.html', podcasts=podcasts)

@main.route('/hotlines')
@login_required
def hotlines():
    hotlines = Event.query.filter(Event.type == 'hotline').all()
    return render_template('hotlines_list.html', hotlines=hotlines)

@main.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        preferences = request.form.get('preferences', '')
        
        # check if email is being changed
        if email != current_user.email:
            # verify email isn't already taken
            existing = db.session.execute(
                text("SELECT user_id FROM user WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if existing and existing[0] != current_user.user_id:
                flash("Email is already in use by another account", "error")
                return redirect(url_for('main.profile'))
        
        success = DBOperations.update_user_profile(
            user_id=current_user.user_id,
            name=name,
            email=email,
            preferences=preferences
        )
        
        if success:
            current_user.name = name
            current_user.email = email
            current_user.preferences = preferences
            
            flash("Profile updated successfully!", "success")
        else:
            flash("Failed to update profile. Please try again.", "error")
        
        return redirect(url_for('main.profile'))
    
    except Exception as e:
        current_app.logger.error(f"Profile update failed: {str(e)}")
        flash("Failed to update profile", "error")
        return redirect(url_for('main.profile'))

from ..forms import ProfileForm, ImageUploadForm
from app.dal.db_operations import DBOperations

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not current_user.is_authenticated:
        flash('You need to log in to access the profile page', 'error')
        return redirect(url_for('main.login'))

    form = ProfileForm(obj=current_user)
    image_form = ImageUploadForm()

    if form.validate_on_submit():
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email is already in use by another account', 'error')
                return redirect(url_for('main.profile'))

        success = DBOperations.update_user_profile(
            user_id=current_user.user_id,
            name=form.name.data,
            email=form.email.data,
            preferences=form.preferences.data
        )

        if success:
            current_user.name = form.name.data
            current_user.email = form.email.data
            current_user.preferences = form.preferences.data
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Failed to update profile. Please try again.', 'error')

    from sqlalchemy import case
    user_notifications = Notification.query.filter_by(user_id=current_user.user_id).order_by(
        case((Notification.sent_at == None, 1), else_=0),
        Notification.sent_at.desc()
    ).all()

    return render_template('profile.html', form=form, image_form=image_form, notifications=user_notifications, survey_completed=False)


from app.forms import ProfileForm 
@main.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        new_password = form.new_password.data

        # Check if the current password matches the one stored in the database
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Incorrect current password', 'error')
            return redirect(url_for('main.change_password'))

        # Hash the new password
        new_password_hash = generate_password_hash(new_password)

        success = DBOperations.change_password(current_user.user_id, new_password_hash)

        if success:
            # Update the current_user object to reflect the new password
            current_user.password_hash = new_password_hash
            flash('Your password has been changed successfully', 'success')
            return redirect(url_for('main.profile'))  
        else:
            flash('Failed to change password. Please try again.', 'error')

    return render_template('change_password.html', form=form)

from werkzeug.security import generate_password_hash, check_password_hash

@main.route('/test_recommend')
def test_recommend_page():
    return render_template('test_recommend.html')

@main.route('/recommend', methods=['POST'])
@limiter.limit("3 per minute") 
def recommend():
    data = request.get_json()
    recommendations = get_llama_recommendation(data)
    return jsonify(recommendations)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        try:
            # Retrieve user by email
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password_hash, password):
                login_user(user)  

                # Check user role first - admin should go to admin dashboard
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))

                # Check for recent surveys in the last 24 hours (only for regular users)
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
        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            flash("Server error during login", "error")

    return render_template('login.html', form=form)

#Only for regular users
@main.route('/no_permission')
def no_permission():
    return render_template('no_permission.html')


import json

@main.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    # Function to format recommendations for display
    def format_recommendations_for_display(recommendations):
        formatted_recs = []
        
        for rec in recommendations:
            # For each recommendation, split it into category, text, and rationale (if available)
            if '•' in rec:
                parts = rec.split('•')[1].split('(')
                formatted_recs.append({
                    'category': parts[0].split(']')[0].strip(' ['),
                    'text': parts[0].split(']')[1].strip(),
                    'rationale': parts[1].strip(')') if len(parts) > 1 else ''
                })
            else:
                formatted_recs.append({
                    'category': 'General',  # Default category if no specific one
                    'text': rec,
                    'rationale': ''
                })
        
        return formatted_recs

    # Check if user has completed a survey in the last 24 hours
    last_survey = MoodSurvey.query.filter_by(user_id=current_user.user_id)\
                                .order_by(MoodSurvey.survey_date.desc())\
                                .first()

    if last_survey and last_survey.survey_date >= datetime.utcnow() - timedelta(hours=24):
        return redirect(url_for('main.mainpage'))
    
    form = MoodSurveyForm()
    
    if form.validate_on_submit():
        try:
            # Prepare the user input for the recommendation system
            user_input = f"""
            Mood Level: {form.mood_level.data}
            Stress Level: {form.stress_level.data}
            Sleep Hours: {form.sleep_hours.data}
            Energy Level: {form.energy_level.data}
            Diet Quality: {form.diet_quality.data}
            Physical Activity: {form.physical_activity.data}
            Spent Time With Someone: {form.spent_time_with_someone.data}
            Feelings Description: {form.feelings_description.data}
            """

            # Get recommendations from Ollama's TinyLLaMA model
            recommendations = get_llama_recommendation(user_input)

            # If the recommendations are returned as a single string, split them into a list
            if isinstance(recommendations, str):
                recommendations = recommendations.split('\n')

            # Format the recommendations for display
            formatted_recs = format_recommendations_for_display(recommendations)

            # Save the survey to the database with the recommendations
            survey_id = DBOperations.create_mood_survey(
                user_id=current_user.user_id,
                mood_level=form.mood_level.data,
                stress_level=form.stress_level.data,
                sleep_hours=form.sleep_hours.data,
                energy_level=form.energy_level.data,
                diet_quality=form.diet_quality.data,
                physical_activity=form.physical_activity.data,
                spent_time_with_someone=form.spent_time_with_someone.data,
                feelings_description=form.feelings_description.data,
                recommendation_text=json.dumps(formatted_recs) # Pass formatted recommendations
            )
            
            if survey_id:
                session['latest_recommendations'] = formatted_recs
                session.modified = True
                return redirect(url_for('main.survey_complete')) 
            
            flash("Error processing your survey. Please try again.", "error")
            
        except Exception as e:
            current_app.logger.error(f"Survey submission error: {str(e)}", exc_info=True)
            flash("Error processing your survey. Please try again.", "error")
    
    return render_template('survey.html', form=form)


@main.route('/history')
@login_required
def history():
    try:
        result = db.session.execute(
            text("CALL GetUserSurveyHistory(:user_id, :limit)"),
            {'user_id': current_user.user_id, 'limit': 10}
        )
        surveys = [dict(row) for row in result]
        for survey in surveys:
            survey['survey_date'] = survey['survey_date'].isoformat()

        return render_template('history.html', surveys=surveys)

    except Exception as e:
        current_app.logger.error(f"Error loading history: {str(e)}")
        return render_template('history.html', surveys=[])


@main.route('/history/chart-data')
@login_required
def chart_data():
    try:
        surveys = db.session.execute(
            text("CALL GetUserSurveyHistory(:user_id, :limit)"),
            {'user_id': current_user.user_id, 'limit': 30}
        ).fetchall()
        
        chart_data = {
            'dates': [row['survey_date'].strftime('%Y-%m-%d') for row in surveys],
            'mood': [row['mood_level'] for row in surveys],
            'stress': [row['stress_level'] for row in surveys]
        }
        return jsonify(chart_data)
        
    except Exception as e:
        current_app.logger.error(f"Chart data error: {str(e)}")
        return jsonify({'error': 'Could not load chart data'}), 500


@main.route('/user/<int:user_id>/charts')
@login_required
def user_charts(user_id):
    try:
        surveys = db.session.execute(
            text("CALL GetUserSurveyHistory(:user_id, :limit)"),
            {'user_id': user_id, 'limit': 30}
        ).fetchall()
        
        # Convert Row objects to dictionaries
        surveys = [dict(survey) for survey in surveys]
        
        # Ensure dates are serializable
        for survey in surveys:
            if 'survey_date' in survey and survey['survey_date']:
                survey['survey_date'] = survey['survey_date'].isoformat()
                
        return render_template('user_charts.html', 
                            user_id=user_id,
                            surveys=surveys)
    except Exception as e:
        current_app.logger.error(f"Error loading charts: {str(e)}")
        return render_template('user_charts.html', 
                            user_id=user_id,
                            surveys=[])
    
from flask import render_template, request, session
from app.controllers.services.recommendations import get_llama_recommendation
from app.model.models import MoodSurvey

import json

@main.route('/survey_complete', methods=['GET'])
@login_required
def survey_complete():
    latest_survey = MoodSurvey.query.filter_by(user_id=current_user.user_id).order_by(MoodSurvey.survey_date.desc()).first()

    if latest_survey:
        try:
            recommendations = json.loads(latest_survey.recommendation_text)
        except Exception:
            recommendations = []

        return render_template('survey_complete.html', recommendations=recommendations)
    else:
        return render_template('survey_complete.html', recommendations=[])



@main.route('/healthcheck')
def health_check():
    """Endpoint to verify database connectivity"""
    try:
        # Simple query to verify database connection
        db.session.execute("SELECT 1")
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': str(e)}), 500

# @main.route('/mainpage')
# @login_required
# def mainpage():
#     return render_template('mainpage.html')  

def build_ai_prompt(analysis, survey_data):
    """Builds a prompt that definitely includes all survey factors"""
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


from werkzeug.security import  generate_password_hash
@main.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        try:
            name = form.name.data
            email = form.email.data
            password = form.password.data
            password_hash = generate_password_hash(password)
            role = 'user'

            # Check if user already exists
            with db.engine.begin() as conn:
                existing_user = conn.execute(
                    text("CALL GetUserByEmail(:email)"),
                    {"email": email}
                ).fetchone()

                if existing_user:
                    flash("Email is already registered.")
                    return render_template('signup.html', form=form)

                result = conn.execute(
                    text("CALL CreateUser(:name, :email, :password_hash, :role)"),
                    {
                        "name": name,
                        "email": email,
                        "password_hash": password_hash,
                        "role": role
                    }
                )

            flash("Account created successfully!")
            return redirect(url_for('main.login'))

        except Exception as e:
            db.session.rollback()
            print(f"CRITICAL ERROR: {str(e)}")
            flash(f"Failed to create account: {str(e)}")

    return render_template('signup.html', form=form)


@main.route('/test-db-connection')
def test_db_connection():
    try:
        # Test raw connection
        with db.engine.connect() as conn:
            result = conn.execute("SELECT 1")
            return f"✓ Database connected! Result: {result.fetchone()}"
    except Exception as e:
        return f"❌ Connection failed: {str(e)}", 500
    
from app.dal.db_operations import DBOperations
from app.sentiment_utils import analyze_sentiment 

from app.controllers.services.recommendations import get_journal_feedback
from langdetect import detect

# @main.route('/journal', methods=['GET', 'POST'])
# @login_required
# def journal_entries():
#     form = JournalEntryForm()
#     feedback_message = None

#     if form.validate_on_submit():
#         # Run sentiment analysis
#         sentiment_type, confidence_score = analyze_sentiment(form.content.data)

#         entry_id = DBOperations.create_journal_entry(
#             user_id=current_user.user_id,
#             content=form.content.data,
#             sentiment_type=sentiment_type,
#             confidence_score=confidence_score
#         )

#         if entry_id:
#             # Generate motivational feedback using TinyLLaMA
#             feedback_message = get_journal_feedback(form.content.data)
#         else:
#             flash("Failed to save journal entry.", "danger")

#     entries = JournalEntry.query.filter_by(user_id=current_user.user_id)\
#         .order_by(JournalEntry.created_at.desc()).all()

#     return render_template(
#         'journal_entries.html',
#         form=form,
#         entries=entries,
#         feedback=feedback_message
#     )

@main.route('/journal', methods=['GET', 'POST'])
@login_required
def journal_entries():
    form = JournalEntryForm()
    feedback_message = None

    if form.validate_on_submit():
        original_text = form.content.data.strip()

        if not original_text:
            flash("Ju lutem shkruani diçka.", "warning")
            return redirect(url_for('main.journal_entries'))

        # Detect language
        lang = detect_language(original_text)

        # Translate to English for sentiment analysis
        translated_text = (
            translate_to_english(original_text) if lang == 'sq' else original_text
        )

        # Run sentiment analysis on the English version
        sentiment_type, confidence_score = analyze_sentiment(translated_text)

        # Save the original version
        entry_id = DBOperations.create_journal_entry(
            user_id=current_user.user_id,
            content=original_text,
            sentiment_type=sentiment_type,
            confidence_score=confidence_score
        )

        if entry_id:
            # Generate motivational feedback (automatically handles translation)
            feedback_message = get_journal_feedback(original_text)
        else:
            flash("Failed to save journal entry.", "danger")

    entries = JournalEntry.query.filter_by(user_id=current_user.user_id)\
        .order_by(JournalEntry.created_at.desc()).all()

    return render_template(
        'journal_entries.html',
        form=form,
        entries=entries,
        feedback=feedback_message
    )

#tpremten jon shtu
from werkzeug.utils import secure_filename
import os

@main.route('/upload-image', methods=['POST'])
@login_required
def upload_image():
    file = request.files.get('image')
    if file:
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'view/static/uploads')
        os.makedirs(upload_folder, exist_ok=True)  

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # Update user's image path 
        current_user.image_url = filename
        db.session.commit()

        flash("Profile image updated!", "success")
    else:
        flash("No file selected", "danger")
    
    return redirect(url_for('main.profile'))


@main.route('/remove_profile_pic', methods=['POST'])
@login_required
def remove_profile_pic():
    # Path to the static uploads folder inside the 'view' directory
    uploads_path = os.path.join(current_app.root_path, '/view/static/uploads')  # Including 'view' folder

    # If the user has a custom image
    if current_user.image_url:
        image_path = os.path.join(uploads_path, current_user.image_url)

        # Delete the file if it exists
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                return jsonify({'success': False, 'message': f'Error deleting image: {str(e)}'}), 500

        # Clear the image URL from the user model
        current_user.image_url = None
        db.session.commit()

        return jsonify({'success': True, 'message': 'Profile picture removed successfully.'})
    
    return jsonify({'success': False, 'message': 'No profile picture to remove.'}), 400




@main.route('/about')
def aboutus_page():
    return render_template('aboutus.html')


from flask_login import logout_user
from flask import redirect, url_for, flash

@main.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))



# import base64
# from flask import request, redirect, url_for, flash, current_app
# from flask_login import login_required, current_user
# from app.controllers.routes import main
# from app import db

# @main.route('/upload-image', methods=['POST'])
# @login_required
# def upload_image():
#     file = request.files.get('image')
#     if file and file.filename:
#         # Read image content and detect MIME type
#         image_data = file.read()
#         mime_type = file.mimetype  # e.g., image/jpeg, image/png, image/webp, etc.

#         # Convert to base64 string
#         encoded = base64.b64encode(image_data).decode('utf-8')
#         base64_string = f"data:{mime_type};base64,{encoded}"

#         # Save to database
#         current_user.image_url = base64_string
#         db.session.commit()

#         flash("Profile image updated!", "success")
#     else:
#         flash("No file selected", "danger")

#     return redirect(url_for('main.profile'))




@main.route('/events')
@login_required
def events_page():
    return render_template('events.html')


#Qikjo i jep me koordinata veq

# from flask import request, jsonify
# import requests
# import os
# from dotenv import load_dotenv
# from flask_login import login_required
# from app.controllers.routes import main

# load_dotenv()

# @main.route('/api/events', methods=['POST'])
# @login_required
# def api_events():
#     data = request.get_json() or {}
#     lat = data.get('lat')
#     lon = data.get('lon')
#     keyword = data.get('keyword')  # optional

#     if not (lat and lon):
#         return jsonify(error='Missing location data'), 400

#     API_KEY = os.getenv('GEOAPIFY_API_KEY')
#     url = 'https://api.geoapify.com/v2/places'

#     categories = 'entertainment,leisure'

#     params = {
#         'categories': categories,
#         'filter': f'circle:{lon},{lat},10000',
#         'limit': 20,
#         'apiKey': API_KEY
#     }

#     if keyword and keyword.strip():
#         params['name'] = keyword.strip()

#     try:
#         resp = requests.get(url, params=params)
#         resp.raise_for_status()
#         payload = resp.json()
#     except requests.RequestException:
#         return jsonify(error='Failed to fetch events.'), 503

#     events = []
#     for feature in payload.get('features', []):
#         prop = feature.get('properties', {})
#         name = prop.get('name')
#         if not name:
#             continue

#         website = prop.get('website', '').strip()
#         lat_prop = prop.get('lat')
#         lon_prop = prop.get('lon')

#         # Skip if neither valid website nor location
#         has_valid_website = False
#         if website:
#             try:
#                 test_resp = requests.head(website, timeout=3)
#                 if test_resp.status_code < 400:
#                     has_valid_website = True
#             except:
#                 pass

#         if not has_valid_website and (not lat_prop or not lon_prop):
#             continue  # skip this event entirely

#         # Build fallback to Google Maps if needed
#         final_url = website if has_valid_website else f'https://www.google.com/maps?q={lat_prop},{lon_prop}'

#         events.append({
#             'name':  name,
#             'date':  'TBD',
#             'venue': prop.get('address_line2', 'Location TBA'),
#             'url':   final_url,
#             'is_map_link': not has_valid_website
#         })

#     return jsonify(events)
#TMIRAT:

from flask import request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

@main.route('/api/events', methods=['POST'])
@login_required
def api_events():
    data = request.get_json() or {}
    lat = data.get('lat')
    lon = data.get('lon')
    keyword = data.get('keyword')  # optional

    if not (lat and lon):
        return jsonify(error='Missing location data'), 400

    API_KEY = os.getenv('GEOAPIFY_API_KEY')  # safer way
    url = 'https://api.geoapify.com/v2/places'

    categories = 'entertainment,leisure'  # or use more specific ones if needed

    params = {
        'categories': categories,
        'filter': f'circle:{lon},{lat},10000',  # 10km search radius
        'limit': 20,
        'apiKey': API_KEY
    }

    if keyword and keyword.strip():
        params['name'] = keyword.strip()

    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException:
        return jsonify(error='Failed to fetch events.'), 503

    events = []
    for feature in payload.get('features', []):
        prop = feature.get('properties', {})
        if not prop.get('name'):
            continue

        # build a Google Maps URL
        lat_prop = prop.get('lat')
        lon_prop = prop.get('lon')
        google_maps_url = f'https://www.google.com/maps?q={lat_prop},{lon_prop}' if lat_prop and lon_prop else ''

        website = prop.get('website', '').strip()

        # If no website, use a Google search for the event's name and location
        search_url = f'https://www.google.com/search?q={prop["name"]}+{prop.get("address_line2", "")}+{lat_prop},{lon_prop}'

        link = website if website else search_url

        events.append({
            'name':        prop['name'],
            'date':        'TBD',  # Geoapify doesn’t give event dates, just places
            'venue':       prop.get('address_line2', 'Location TBA'),
            'url':         link, 
            'is_map_link': not bool(website)  # Label for Google search or Website
        })

    return jsonify(events)



# from app.dal.db_operations import DBOperations

# @main.route('/notifications/create', methods=['POST'])
# @login_required
# def create_notification_route():
#     try:
#         message = request.form.get('message')
#         type_ = request.form.get('type')  # 'survey', 'journal', or 'mindfulness'
        
#         if type_ not in ['survey', 'journal', 'mindfulness']:
#             flash('Invalid notification type', 'error')
#             return redirect(url_for('main.profile'))

#         if not message or not type_:
#             flash('Missing message or type', 'error')
#             return redirect(url_for('main.profile'))

#         success = DBOperations.create_notification(
#             user_id=current_user.user_id,
#             message=message,
#             type_=type_
#         )

#         if success:
#             flash('Notification created successfully!', 'success')
#         else:
#             flash('Failed to create notification.', 'error')

#         return redirect(url_for('main.profile'))

#     except Exception as e:
#         current_app.logger.error(f"Notification creation failed: {str(e)}")
#         flash('Failed to create notification', 'error')
#         return redirect(url_for('main.profile'))



#per notifications
from app.dal.db_operations import DBOperations


def get_user_notifications(user_id):
    return Notification.query.filter(
        (Notification.user_id == user_id) | (Notification.user_id == None),
        Notification.status == 'pending'
    ).all()


#jon shtu 
from flask import flash, redirect, url_for, request, current_app, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.dal.db_operations import DBOperations
from app.model.models import Notification  # Make sure Notification is imported


# @main.route('/mainpage')
# @login_required
# def mainpage():
#     try:
#         # Run survey check and notify if needed
#         DBOperations.check_survey_and_notify(user_id=current_user.user_id)
#     except Exception as e:
#         current_app.logger.error(f"Survey check failed on mainpage: {str(e)}")
#         flash('An error occurred while checking the survey.', 'error')

#     # Fetch pending notifications
#     pending_notifications = Notification.query.filter(
#         or_(
#             Notification.user_id == current_user.user_id,
#             Notification.user_id == None
#         ),
#         Notification.status == 'pending'
#     ).all()

#     return render_template('mainpage.html', pending_notifications=pending_notifications)



# @main.route('/notifications/create', methods=['POST'])
# @login_required
# def create_notification_route():
#     try:
#         message = request.form.get('message')
#         type_ = request.form.get('type')  # 'survey', 'journal', or 'mindfulness'

#         if type_ not in ['survey', 'journal', 'mindfulness']:
#             flash('Invalid notification type', 'error')
#             return redirect(url_for('main.profile'))

#         if not message:
#             flash('Notification message is required', 'error')
#             return redirect(url_for('main.profile'))

#         success = DBOperations.create_notification(
#             user_id=current_user.user_id,
#             message=message,
#             type_=type_
#         )

#         if success:
#             flash('Notification created successfully!', 'success')
#         else:
#             flash('Failed to create notification.', 'error')

#         return redirect(url_for('main.profile'))

#     except Exception as e:
#         current_app.logger.error(f"Notification creation failed: {str(e)}")
#         flash('Failed to create notification', 'error')
#         return redirect(url_for('main.profile'))

# import logging
# from app.model.models import SurveyResponse, Notification
# from app import db

# class DBOperations:
#     @staticmethod
#     def check_survey_and_notify(user_id):
#         # Check if the user has completed the survey
#         survey_completed = SurveyResponse.query.filter_by(user_id=user_id).first() is not None

#         if not survey_completed:
#             # Check if a pending notification already exists
#             existing_notification = Notification.query.filter_by(
#                 user_id=user_id,
#                 type='survey',
#                 status='pending'
#             ).first()

#             if not existing_notification:
#                 # Create a new notification
#                 notification = Notification(
#                     user_id=user_id,
#                     message='Please complete your survey.',
#                     type='survey',
#                     status='pending'
#                 )
#                 db.session.add(notification)
#                 db.session.commit()
#                 return True
#         return False


#u shtun tshtunen
def get_user_notifications(user_id):
    return Notification.query.filter(
        (Notification.user_id == user_id) | (Notification.user_id == None),
        Notification.status == 'pending'
    ).all()

from sqlalchemy import or_

@main.route('/mainpage')
@login_required
def mainpage():
    # Check for incomplete survey
    today = date.today()
    last_survey = MoodSurvey.query.filter(
        MoodSurvey.user_id == current_user.user_id,
        db.func.date(MoodSurvey.survey_date) == today
    ).first()

    # If no survey today, create notification
    if not last_survey:
        notification = Notification(
            user_id=current_user.user_id,
            message="📝 Please complete your daily mood survey, so we can help you!",
            type='survey',
            status='pending'
        )
        db.session.add(notification)
        db.session.commit()

    # Get all pending notifications
    pending_notifications = Notification.query.filter(
        or_(
            Notification.user_id == current_user.user_id,
            Notification.user_id == None
        ),
        Notification.status == 'pending'
    ).all()
    
    return render_template('mainpage.html', pending_notifications=pending_notifications)


@main.route('/notifications/create', methods=['POST'])
@login_required
def create_notification_route():
    try:
        message = request.form.get('message')
        type_ = request.form.get('type')  # 'survey', 'journal', or 'mindfulness'
        
        if type_ not in ['survey', 'journal', 'mindfulness']:
            flash('Invalid notification type', 'error')
            return redirect(url_for('main.profile'))

        if not message or not type_:
            flash('Missing message or type', 'error')
            return redirect(url_for('main.profile'))

        success = DBOperations.create_notification(
            user_id=current_user.user_id,
            message=message,
            type_=type_
        )

        if success:
            flash('Notification created successfully!', 'success')
        else:
            flash('Failed to create notification.', 'error')

        return redirect(url_for('main.profile'))

    except Exception as e:
        current_app.logger.error(f"Notification creation failed: {str(e)}")
        flash('Failed to create notification', 'error')
        return redirect(url_for('main.profile'))



#per stored procedure te re
@main.route('/notifications/check-survey', methods=['POST'])
@login_required
def check_survey_and_notify_route():
    try:
        success = DBOperations.check_survey_and_notify(user_id=current_user.user_id)

        if success:
            flash('Survey check completed.', 'success')
        else:
            flash('Survey check failed.', 'error')

        return redirect(url_for('main.profile'))

    except Exception as e:
        current_app.logger.error(f"Survey check failed: {str(e)}")
        flash('An error occurred while checking the survey.', 'error')
        return redirect(url_for('main.profile'))