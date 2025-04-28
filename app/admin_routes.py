# from flask import Blueprint, render_template, redirect, url_for, flash, request
# from flask_login import login_required, current_user
# from app.models import User, Event, MoodSurvey, db
# from app.forms import EventForm
# from app.utils import admin_required

# admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# # Admin Dashboard Route
# @admin_bp.route('/dashboard')
# @admin_required
# def dashboard():
#     users = User.query.all()
#     events = Event.query.order_by(Event.date_time.desc()).limit(5).all()
#     surveys = MoodSurvey.query.order_by(MoodSurvey.created_at.desc()).limit(5).all()
#     return render_template('admin/dashboard.html', users=users, events=events, surveys=surveys)

# # Manage Users
# @admin_bp.route('/users')
# @admin_required
# def manage_users():
#     users = User.query.all()
#     return render_template('admin/manage_users.html', users=users)

# @admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
# @admin_required
# def delete_user(user_id):
#     user = User.query.get_or_404(user_id)
    
#     try:
#         # Delete the user's associated surveys
#         MoodSurvey.query.filter_by(user_id=user_id).delete()

#         # Then delete the user
#         db.session.delete(user)
#         db.session.commit()

#         flash('User and their surveys have been deleted successfully.', 'success')
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Error deleting user: {e}', 'error')

#     return redirect(url_for('admin.manage_users'))


# # Manage Events
# @admin_bp.route('/events')
# @admin_required
# def manage_events():
#     events = Event.query.all()
#     return render_template('admin/manage_events.html', events=events)

# @admin_bp.route('/event/delete/<int:event_id>', methods=['POST'])
# @admin_required
# def delete_event(event_id):
#     event = Event.query.get_or_404(event_id)
#     db.session.delete(event)
#     db.session.commit()
#     flash('Event deleted successfully.', 'success')
#     return redirect(url_for('admin.manage_events'))


# # Add New Event
# @admin_bp.route('/events/add', methods=['GET', 'POST'])
# @admin_required
# def add_event():
#     if current_user.role != 'admin':
#         flash("You do not have the necessary permissions.", "danger")
#         return redirect(url_for('main.mainpage'))

#     form = EventForm()
#     if form.validate_on_submit():
#         new_event = Event(
#             title=form.title.data,
#             location=form.location.data,
#             description=form.description.data,
#             date_time=form.date_time.data,
#             type=form.type.data,
#             link=form.link.data
#         )
#         db.session.add(new_event)
#         db.session.commit()
#         flash("Event added successfully!", "success")
#         return redirect(url_for('admin.manage_events'))  # Redirecting back to events management

#     return render_template('admin/add_event.html', form=form)


# # View Events for Admin
# @admin_bp.route('/events/view')
# @admin_required
# def admin_events():
#     if current_user.role != 'admin':
#         flash("You do not have the necessary permissions.", "danger")
#         return redirect(url_for('main.mainpage'))

#     events = Event.query.all()
#     return render_template('admin/events.html', events=events)


from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import User, Event, MoodSurvey, db
from app.forms import EventForm, HotlineForm, PodcastForm  # You can create specific forms for Podcasts/Hotlines as needed
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Admin Dashboard Route
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    users = User.query.all()
    events = Event.query.order_by(Event.date_time.desc()).limit(5).all()
    surveys = MoodSurvey.query.order_by(MoodSurvey.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', users=users, events=events, surveys=surveys)


@admin_bp.route('/add/podcast', methods=['GET', 'POST'])
@admin_required
def add_podcast():
    form = PodcastForm()
    resource_type = 'podcast'  # Add this line to define the resource_type

    if form.validate_on_submit():
        new_podcast = Event(
            title=form.title.data,
            description=form.description.data,
            type='podcast',  # Type should be podcast
            link=form.link.data
        )
        db.session.add(new_podcast)
        db.session.commit()
        flash('Podcast added successfully!', 'success')
        return redirect(url_for('admin.manage_podcasts'))

    return render_template('admin/add_podcast.html', form=form, resource_type=resource_type)

@admin_bp.route('/add/hotline', methods=['GET', 'POST'])
@admin_required
def add_hotline():
    form = HotlineForm()
    if form.validate_on_submit():
        new_hotline = Event(
            title=form.title.data,
            phone_number=form.phone_number.data,
            description=form.description.data,
            type='hotline',  # Type should be hotline
        )
        db.session.add(new_hotline)
        db.session.commit()
        flash('Hotline added successfully!', 'success')
        return redirect(url_for('admin.manage_hotlines'))

    return render_template('admin/add_hotline.html', form=form)

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
    events = Event.query.filter(Event.type == 'event').all()  # Filter by event type
    return render_template('admin/manage_events.html', events=events)

@admin_bp.route('/event/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('admin.manage_events'))


# Manage Podcasts
@admin_bp.route('/podcasts')
@admin_required
def manage_podcasts():
    podcasts = Event.query.filter(Event.type == 'podcast').all()  # Filter by podcast type
    return render_template('admin/manage_podcasts.html', podcasts=podcasts)

@admin_bp.route('/podcast/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_podcast(event_id):
    podcast = Event.query.get_or_404(event_id)
    db.session.delete(podcast)
    db.session.commit()
    flash('Podcast deleted successfully.', 'success')
    return redirect(url_for('admin.manage_podcasts'))


# Manage Hotlines
@admin_bp.route('/hotlines')
@admin_required
def manage_hotlines():
    hotlines = Event.query.filter(Event.type == 'hotline').all()  # Filter by hotline type
    return render_template('admin/manage_hotlines.html', hotlines=hotlines)

@admin_bp.route('/hotline/delete/<int:event_id>', methods=['POST'])
@admin_required
def delete_hotline(event_id):
    hotline = Event.query.get_or_404(event_id)
    db.session.delete(hotline)
    db.session.commit()
    flash('Hotline deleted successfully.', 'success')
    return redirect(url_for('admin.manage_hotlines'))


# # Add New Event, Podcast, or Hotline
# @admin_bp.route('/add/<resource_type>', methods=['GET', 'POST'])
# @admin_required
# def add_resource(resource_type):
#     if resource_type not in ['event', 'podcast', 'hotline']:
#         flash("Invalid resource type.", "danger")
#         return redirect(url_for('admin.dashboard'))

#     form = EventForm()  # Create forms specific to the resource type if needed
#     if form.validate_on_submit():
#         new_resource = Event(
#             title=form.title.data,
#             location=form.location.data,
#             description=form.description.data,
#             date_time=form.date_time.data,
#             type=resource_type,  # Set the type based on the resource
#             link=form.link.data
#         )
#         db.session.add(new_resource)
#         db.session.commit()
#         flash(f"{resource_type.capitalize()} added successfully!", "success")
#         return redirect(url_for(f'admin.manage_{resource_type}s'))  # Redirect dynamically based on type

#     return render_template(f'admin/add_{resource_type}.html', form=form)

@admin_bp.route('/add/<resource_type>', methods=['GET', 'POST'])
@admin_required
def add_resource(resource_type):
    if resource_type not in ['event', 'podcast', 'hotline']:
        flash("Invalid resource type.", "danger")
        return redirect(url_for('admin.dashboard'))

    # Dynamically assign the form based on resource_type
    if resource_type == 'event':
        form = EventForm()
    elif resource_type == 'podcast':
        form = PodcastForm()
    else:
        form = HotlineForm()

    if form.validate_on_submit():
        # Dynamically set fields for each type
        if resource_type == 'event':
            new_resource = Event(
                title=form.title.data,
                location=form.location.data,
                description=form.description.data,
                date_time=form.date_time.data,
                type=resource_type,  # 'event'
                link=form.link.data
            )
        elif resource_type == 'podcast':
            new_resource = Event(
                title=form.title.data,
                description=form.description.data,
                type=resource_type,  # 'podcast'
                link=form.link.data
            )
        elif resource_type == 'hotline':
            new_resource = Event(
                title=form.title.data,
                phone_number=form.phone_number.data,
                description=form.description.data,
                type=resource_type,  # 'hotline'
            )

        # Add to database and commit
        db.session.add(new_resource)
        db.session.commit()
        flash(f"{resource_type.capitalize()} added successfully!", "success")
        return redirect(url_for(f'admin.manage_{resource_type}s'))  # Redirect dynamically based on type

    # Pass resource_type to the template explicitly
    return render_template(f'admin/add_{resource_type}.html', form=form, resource_type=resource_type)
