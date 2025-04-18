from sqlalchemy import text
from flask import Blueprint, current_app, json, jsonify, render_template, request, redirect, url_for, flash, session
from flask_limiter import Limiter
from flask_login import login_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy  # Import SQLAlchemy
from app.services.recommendations import generate_recommendations
from .models import db, Recommendation, User, MoodSurvey
from .forms import ChangePasswordForm, MoodSurveyForm, LoginForm, SignupForm
from datetime import date, timedelta
from datetime import datetime
from flask_limiter.util import get_remote_address
import openai  # Add this with your other imports
from app.db_operations import DBOperations
from app.models import JournalEntry



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



@main.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        preferences = request.form.get('preferences', '')
        
        # Check if email is being changed
        if email != current_user.email:
            # Verify email isn't already taken
            existing = db.session.execute(
                text("SELECT user_id FROM user WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if existing and existing[0] != current_user.user_id:
                flash("Email is already in use by another account", "error")
                return redirect(url_for('main.profile'))
        
        # Update profile using stored procedure
        success = DBOperations.update_user_profile(
            user_id=current_user.user_id,
            name=name,
            email=email,
            preferences=preferences
        )
        
        if success:
            # Update Flask-Login's user object
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


from .forms import ProfileForm
from .db_operations import DBOperations

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if not current_user.is_authenticated:
        flash('You need to log in to access the profile page', 'error')
        return redirect(url_for('main.login'))  # Redirect to login explicitly if not authenticated
    
    form = ProfileForm(obj=current_user)  # Auto-populate form with current user data
    
    if form.validate_on_submit():
        # Check if email is being changed to one that already exists
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email is already in use by another account', 'error')
                return redirect(url_for('main.profile'))
        
        # Update profile using stored procedure
        success = DBOperations.update_user_profile(
            user_id=current_user.user_id,
            name=form.name.data,
            email=form.email.data,
            preferences=form.preferences.data
        )
        
        if success:
            # Update the current_user object to reflect changes immediately
            current_user.name = form.name.data
            current_user.email = form.email.data
            current_user.preferences = form.preferences.data
            flash('Your profile has been updated!', 'success')
            return redirect(url_for('main.profile'))
        else:
            flash('Failed to update profile. Please try again.', 'error')
    
    return render_template('profile.html', form=form)


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

        # Call the stored procedure to change the password
        success = DBOperations.change_password(current_user.user_id, new_password_hash)

        if success:
            # Update the current_user object to reflect the new password
            current_user.password_hash = new_password_hash
            flash('Your password has been changed successfully', 'success')
            return redirect(url_for('main.profile'))  # Or wherever you want to redirect
        else:
            flash('Failed to change password. Please try again.', 'error')

    return render_template('change_password.html', form=form)

from werkzeug.security import generate_password_hash, check_password_hash


@main.route('/recommend', methods=['POST'])
@limiter.limit("3 per minute") 
def recommend():
    data = request.get_json()
    recommendations = generate_recommendations(data)
    return jsonify(recommendations)

# Login route
# @main.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         email = form.email.data
#         password = form.password.data
        
#         user = User.query.filter_by(email=email).first()
        
#         if user and user.check_password(password):
#             login_user(user)
            
#             # Check for surveys in last 24 hours
#             twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
#             recent_survey = MoodSurvey.query.filter(
#                 MoodSurvey.user_id == user.user_id,
#                 MoodSurvey.survey_date >= twenty_four_hours_ago
#             ).first()
            
#             if recent_survey:
#                 return redirect(url_for('main.mainpage'))
#             else:
#                 return redirect(url_for('main.survey'))
        
#         flash("Invalid credentials", "error")
        
#     return render_template('login.html', form=form)


from sqlalchemy import text

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        try:
            # Call stored procedure to get user
            with db.engine.connect() as conn:
                result = conn.execute(
                    text("CALL GetUserByEmail(:email)"),
                    {"email": email}
                )
                user_row = result.fetchone()
                result.close()

            if user_row:
                # You need to manually compare password if using stored procedures
                stored_password_hash = user_row['password_hash']
                from werkzeug.security import check_password_hash
                
                if check_password_hash(stored_password_hash, password):
                    # Manually load user object for login_user
                    user = User(
                        user_id=user_row['user_id'],
                        name=user_row['name'],
                        email=user_row['email'],
                        password_hash=stored_password_hash,
                        role=user_row['role']
                    )
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

        except Exception as e:
            print(f"CRITICAL ERROR: {str(e)}")
            flash("Server error during login", "error")
    
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



# @main.route('/survey-history')
# @login_required
# def survey_history():
#     surveys = DBOperations.get_user_survey_history(current_user.user_id)
#     return render_template('survey_history.html', surveys=surveys)


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

# @main.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignupForm()
#     if form.validate_on_submit():
#         try:
#             # Correct way to create a user
#             new_user = User(
#                 name=str(form.name.data),  # Note the comma after each argument
#                 email=str(form.email.data)  # No comma after last argument
#             )
#             new_user.set_password(str(form.password.data))  # Single closing parenthesis
            
#             db.session.add(new_user)
#             db.session.commit()  # <-- THIS MUST SUCCEED
            
#             # Verify the user was actually saved
#             test_user = User.query.filter_by(email=form.email.data).first()
#             if not test_user:
#                 raise Exception("User disappeared after commit!")
                
#             flash("Account created!")
#             return redirect(url_for('main.login'))
            
#         except Exception as e:
#             db.session.rollback()
#             print(f"CRITICAL ERROR: {str(e)}")  # Check console
#             flash("Failed to create account (server error)")
    
#     return render_template('signup.html', form=form)



# from werkzeug.security import check_password_hash, generate_password_hash
# @main.route('/signup', methods=['GET', 'POST'])
# def signup():
#     form = SignupForm()
#     if form.validate_on_submit():
#         try:
#             # Get data from the form
#             name = form.name.data
#             email = form.email.data
#             password = form.password.data  # Plain password from the form

#             # Hash the password before passing it to the stored procedure
#             password_hash = generate_password_hash(password)

#             # Assuming 'user' is the default role for new users
#             role = 'user'  # You can set this to 'admin' if you want an admin role

#             # Use SQLAlchemy's engine to call the stored procedure with 4 parameters
#             with db.engine.begin() as conn:
#                 result = conn.execute(
#                     text("CALL CreateUser(:name, :email, :password_hash, :role)"),
#                     {"name": name, "email": email, "password_hash": password_hash, "role": role}
#                 )

#             # Check if the procedure executed and inserted data
#             if result.rowcount == 0:
#                 raise Exception("Stored procedure failed to insert user.")

#             flash("Account created successfully!")
#             return redirect(url_for('main.login'))  # Redirect to the login page

#         except Exception as e:
#             db.session.rollback()
#             print(f"CRITICAL ERROR: {str(e)}")  # Log more details
#             flash(f"Failed to create account: {str(e)}")  # Provide error details

#     return render_template('signup.html', form=form)


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

                # Call CreateUser stored procedure
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
    



    #qitu kom shtu palidhje 
# @main.route('/upload-image', methods=['POST'])
# @login_required
# def upload_image():
#     file = request.files.get('image')
#     if file:
#         filename = secure_filename(file.filename)
#         file_path = os.path.join('static/uploads', filename)
#         file.save(file_path)

#         # Update user's image path (adjust depending on your model)
#         current_user.image_url = filename  # Save only the filename, not the full path
#         db.session.commit()

#         flash("Profile image updated!", "success")
#     else:
#         flash("No file selected", "danger")
    
#     return redirect(url_for('main.profile'))
from app.forms import JournalEntryForm


# @main.route('/journal', methods=['GET', 'POST'])
# @login_required
# def journal_entries():
#     form = JournalEntryForm()
#     if form.validate_on_submit():
#         new_entry = JournalEntry(user_id=current_user.user_id, content=form.content.data)
#         db.session.add(new_entry)
#         db.session.commit()
#         flash('Journal entry saved.', 'success')
#         return redirect(url_for('main.journal_entries'))

#     entries = JournalEntry.query.filter_by(user_id=current_user.user_id).order_by(JournalEntry.created_at.desc()).all()
#     return render_template('journal_entries.html', form=form, entries=entries)
@main.route('/journal', methods=['GET', 'POST'])
@login_required
def journal_entries():
    form = JournalEntryForm()
    if form.validate_on_submit():
        new_entry = JournalEntry(
            content=form.content.data,
            user_id=current_user.user_id
        )
        db.session.add(new_entry)
        db.session.commit()

        # Optional: Do sentiment analysis here, if set up
        return redirect(url_for('main.mainpage'))  # 👈 redirect to main page after saving

    entries = JournalEntry.query.filter_by(user_id=current_user.user_id)\
        .order_by(JournalEntry.created_at.desc()).all()
    return render_template('journal_entries.html', form=form, entries=entries)
