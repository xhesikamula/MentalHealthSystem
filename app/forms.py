from flask_wtf import FlaskForm
from wtforms import (IntegerField, TextAreaField, SelectField, FloatField,
                    StringField, PasswordField, SubmitField)
from wtforms.validators import (DataRequired, NumberRange, Email, Length, 
                            EqualTo, ValidationError)
from app.models import User

from flask_wtf.file import FileField, FileAllowed

from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField

class ImageUploadForm(FlaskForm):
    image = FileField('Upload Profile Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Upload Image')

from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired

class JournalEntryForm(FlaskForm):
    content = TextAreaField('New Journal Entry', validators=[DataRequired()])
    submit = SubmitField('Save Entry')


class MoodSurveyForm(FlaskForm):
    mood_level = IntegerField('Mood Level (1-10)', 
                            validators=[DataRequired(), 
                                    NumberRange(min=1, max=10)],
                            render_kw={"placeholder": "1 (worst) to 10 (best)"})
    
    stress_level = IntegerField('Stress Level (1-10)', 
                            validators=[DataRequired(), 
                                        NumberRange(min=1, max=10)],
                            render_kw={"placeholder": "1 (low) to 10 (high)"})
    
    sleep_hours = FloatField('Hours of Sleep', 
                        validators=[DataRequired(), 
                                    NumberRange(min=0, max=24)],
                        render_kw={"placeholder": "0 to 24 hours"})
    
    energy_level = IntegerField('Energy Level (1-10)', 
                            validators=[DataRequired(), 
                                        NumberRange(min=1, max=10)],
                            render_kw={"placeholder": "1 (low) to 10 (high)"})
    
    diet_quality = IntegerField('Diet Quality (1-10)', 
                            validators=[DataRequired(), 
                                        NumberRange(min=1, max=10)],
                            render_kw={"placeholder": "1 (poor) to 10 (excellent)"})
    
    physical_activity = IntegerField('Physical Activity Level (0-10)', 
                                validators=[NumberRange(min=0, max=10)],
                                render_kw={"placeholder": "0 (none) to 10 (intense)"})
    
    spent_time_with_someone = SelectField(
        'Did you spend time with someone today?',
        choices=[('yes', 'Yes'), ('no', 'No')],
        validators=[DataRequired()]
    )
    
    feelings_description = TextAreaField('How are you feeling today?',
                                    render_kw={"placeholder": "Describe your feelings..."})
    
    submit = SubmitField('Submit Survey')


class LoginForm(FlaskForm):
    email = StringField('Email', 
                    validators=[DataRequired(), Email()],
                    render_kw={"placeholder": "Your email address"})
    
    password = PasswordField('Password', 
                        validators=[DataRequired()],
                        render_kw={"placeholder": "Your password"})
    
    submit = SubmitField('Log In')


class SignupForm(FlaskForm):
    name = StringField('Full Name', 
                    validators=[DataRequired(), Length(min=2, max=100)],
                    render_kw={"placeholder": "Your full name"})
    
    email = StringField('Email', 
                    validators=[DataRequired(), Email()],
                    render_kw={"placeholder": "Your email address"})
    
    password = PasswordField('Password', 
                        validators=[DataRequired(), Length(min=6)],
                        render_kw={"placeholder": "At least 6 characters"})
    
    confirm_password = PasswordField('Confirm Password',
                                validators=[DataRequired(), 
                                            EqualTo('password', 
                                                    message='Passwords must match')],
                                render_kw={"placeholder": "Re-enter your password"})
    
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')
        

from wtforms.validators import DataRequired, EqualTo, Length, Email
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField


class ProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    preferences = TextAreaField('Preferences')




class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('confirm_password', message='Passwords must match')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired()])
