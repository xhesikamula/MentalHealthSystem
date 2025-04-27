# app/admin_routes.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.models import User, Event, MoodSurvey, db
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    users = User.query.all()
    events = Event.query.order_by(Event.date_time.desc()).limit(5).all()
    surveys = MoodSurvey.query.order_by(MoodSurvey.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', users=users, events=events, surveys=surveys)

# Manage Users
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    try:
        # Delete the user's associated surveys
        MoodSurvey.query.filter_by(user_id=user_id).delete()

        # Then delete the user
        db.session.delete(user)
        db.session.commit()

        flash('User and their surveys have been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {e}', 'error')

    return redirect(url_for('admin.manage_users'))


# Manage Events
@admin_bp.route('/events')
@admin_required
def manage_events():
    events = Event.query.all()
    return render_template('admin/manage_events.html', events=events)

@admin_bp.route('/event/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.manage_events'))
