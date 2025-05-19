from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms import EventForm, HotlineForm, PodcastForm
from app.utils import admin_required
from app.model.models import Event

from app.dal.db_operations import (
    get_all_users, delete_user_and_surveys,
    get_recent_events, get_events_by_type,
    delete_event_by_id, add_new_event,
    get_recent_surveys, update_event_by_id, update_hotline_by_id, update_podcast_by_id
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    users = get_all_users()
    events = get_recent_events()
    surveys = get_recent_surveys()
    return render_template('admin/dashboard.html', users=users, events=events, surveys=surveys)


# --- ADD Podcast ---
@admin_bp.route('/add/podcast', methods=['GET', 'POST'])
@admin_required
def add_podcast():
    form = PodcastForm()
    resource_type = 'podcast'

    if form.validate_on_submit():
        new_podcast = Event(
            title=form.title.data,
            description=form.description.data,
            type='podcast',
            link=form.link.data
        )
        add_new_event(new_podcast)
        flash('Podcast added successfully!', 'success')
        return redirect(url_for('admin.manage_podcasts'))

    return render_template('admin/add_podcast.html', form=form, resource_type=resource_type)


# --- ADD Hotline ---
@admin_bp.route('/add/hotline', methods=['GET', 'POST'])
@admin_required
def add_hotline():
    form = HotlineForm()
    if form.validate_on_submit():
        new_hotline = Event(
            title=form.title.data,
            description=form.description.data,
            type='hotline',
            phone_number=form.phone_number.data 
        )
        
        add_new_event(new_hotline)
        flash('Hotline added successfully!', 'success')
        return redirect(url_for('admin.manage_hotlines'))

    return render_template('admin/add_hotline.html', form=form)


# --- MANAGE USERS ---
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = get_all_users()
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    result = delete_user_and_surveys(user_id)
    if result == True:
        flash('User and their surveys have been deleted successfully.', 'success')
    else:
        flash(f'Error deleting user: {result}', 'error')
    return redirect(url_for('admin.manage_users'))


# --- MANAGE EVENTS ---
@admin_bp.route('/events')
@admin_required
def manage_events():
    events = get_events_by_type('event')
    return render_template('admin/manage_events.html', events=events)

@admin_bp.route('/event/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    delete_event_by_id(event_id)
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.manage_events'))



@admin_bp.route('/event/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm(obj=event)

    if form.validate_on_submit():
        result = update_event_by_id(
            event_id,
            form.title.data,
            form.location.data,
            form.description.data,
            form.date_time.data,
            form.link.data,
            form.image_url.data 
        )
        if result is True:
            flash('Event updated successfully.', 'success')
        else:
            flash(f'Error updating event: {result}', 'danger')
        return redirect(url_for('admin.manage_events'))

    return render_template('admin/edit_event.html', form=form, resource_type='event')




# --- MANAGE PODCASTS ---
@admin_bp.route('/podcasts')
@admin_required
def manage_podcasts():
    podcasts = get_events_by_type('podcast')
    return render_template('admin/manage_podcasts.html', podcasts=podcasts)

@admin_bp.route('/podcast/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_podcast(event_id):
    delete_event_by_id(event_id)
    flash('Podcast deleted successfully.', 'success')
    return redirect(url_for('admin.manage_podcasts'))

@admin_bp.route('/podcast/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_podcast(event_id):
    podcast = Event.query.get_or_404(event_id)
    form = PodcastForm(obj=podcast)

    if form.validate_on_submit():
        result = update_podcast_by_id(
            event_id,
            form.title.data,
            form.description.data,
            form.link.data,
            form.image_url.data
        )
        if result is True:
            flash('Podcast updated successfully.', 'success')
        else:
            flash(f'Error updating podcast: {result}', 'danger')
        return redirect(url_for('admin.manage_podcasts'))

    return render_template('admin/edit_podcast.html', form=form, resource_type='podcast')


# --- MANAGE HOTLINES ---
@admin_bp.route('/hotlines')
@admin_required
def manage_hotlines():
    hotlines = get_events_by_type('hotline')
    return render_template('admin/manage_hotlines.html', hotlines=hotlines)

@admin_bp.route('/hotline/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_hotline(event_id):
    delete_event_by_id(event_id)
    flash('Hotline deleted successfully.', 'success')
    return redirect(url_for('admin.manage_hotlines'))


@admin_bp.route('/hotline/edit/<int:event_id>', methods=['GET', 'POST'])
@admin_required
def edit_hotline(event_id):
    hotline = Event.query.get_or_404(event_id)
    form = HotlineForm(obj=hotline)

    if form.validate_on_submit():
        result = update_hotline_by_id(
            event_id,
            form.title.data,
            form.description.data,
            form.phone_number.data
        )
        if result is True:
            flash('Hotline updated successfully.', 'success')
        else:
            flash(f'Error updating hotline: {result}', 'danger')
        return redirect(url_for('admin.manage_hotlines'))

    return render_template('admin/edit_hotline.html', form=form, resource_type='hotline')


# --- ADD Resource (dynamic for event, podcast, hotline) ---
@admin_bp.route('/add/<resource_type>', methods=['GET', 'POST'])
@admin_required
def add_resource(resource_type):
    if resource_type not in ['event', 'podcast', 'hotline']:
        flash("Invalid resource type.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Choose correct form
    if resource_type == 'event':
        form = EventForm()
    elif resource_type == 'podcast':
        form = PodcastForm()
    else:
        form = HotlineForm()

    if form.validate_on_submit():
        if resource_type == 'event':
            new_resource = Event(
                title=form.title.data,
                location=form.location.data,
                description=form.description.data,
                date_time=form.date_time.data,
                type=resource_type,
                link=form.link.data,
                image_url=form.image_url.data 
               
            )
        elif resource_type == 'podcast':
            new_resource = Event(
                title=form.title.data,
                description=form.description.data,
                type=resource_type,
                link=form.link.data
                
            )
        elif resource_type == 'hotline':
            new_resource = Event(
                title=form.title.data,
                phone_number=form.phone_number.data,
                description=form.description.data,
                type=resource_type
                
            )

        add_new_event(new_resource)
        flash(f"{resource_type.capitalize()} added successfully!", "success")
        return redirect(url_for(f'admin.manage_{resource_type}s'))

    return render_template(f'admin/add_{resource_type}.html', form=form, resource_type=resource_type)
