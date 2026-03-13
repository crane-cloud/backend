from datetime import datetime, timedelta

import click
from sqlalchemy import Date, cast, or_

from app.helpers.inactiveUser_notification import send_inactive_notification_to_user
from app.models import db
from app.models.user import User


def find_user_by_email_or_username(identifier):
    """
    Find a user by either email or username

    Args:
        identifier (str): Email address or username

    Returns:
        User: User object if found, None otherwise
    """
    if not identifier:
        return None

    # First try to find by email
    user = User.find_first(email=identifier)
    if user:
        return user

    # If not found by email, try by username
    user = User.find_first(username=identifier)
    if user:
        return user

    return None


def is_email_or_username(identifier):
    """
    Check if the identifier looks like an email or username

    Args:
        identifier (str): String to check

    Returns:
        str: 'email' if it looks like an email, 'username' otherwise
    """
    if not identifier:
        return 'username'

    # Simple email check - contains @ and has domain structure
    if '@' in identifier and '.' in identifier.split('@')[1]:
        return 'email'

    return 'username'


def validate_login_identifier(identifier):
    """
    Validate login identifier (email or username)

    Args:
        identifier (str): Email or username to validate

    Returns:
        dict: Result with 'valid' (bool), 'type' (str), and 'message' (str)
    """
    result = {
        'valid': False,
        'type': None,
        'message': ''
    }

    if not identifier:
        result['message'] = 'Login identifier is required'
        return result

    if not isinstance(identifier, str):
        result['message'] = 'Login identifier must be a string'
        return result

    identifier = identifier.strip()
    if not identifier:
        result['message'] = 'Login identifier cannot be empty'
        return result

    # Determine if it's email or username
    identifier_type = is_email_or_username(identifier)
    result['type'] = identifier_type

    if identifier_type == 'email':
        # Basic email validation
        if len(identifier) < 5 or len(identifier) > 254:
            result['message'] = 'Email address is too short or too long'
            return result

        # Check for basic email format
        if not '@' in identifier or not '.' in identifier.split('@')[1]:
            result['message'] = 'Invalid email format'
            return result
    else:
        # Username validation
        if len(identifier) < 3 or len(identifier) > 30:
            result['message'] = 'Username must be between 3 and 30 characters'
            return result

        # Check username format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', identifier):
            result['message'] = 'Username can only contain letters, numbers, underscores, and hyphens'
            return result

    result['valid'] = True
    return result


def get_inactive_users_query(
    start_days_ago=None,
    end_days_ago=None,
    days_range=None,
    keywords=None,
    disabled_param=None,
    created_date_param=None,
    reminder_since=None,
):
    """
    Get the query for inactive users
    """
    today = datetime.now().date()

    if start_days_ago is not None and end_days_ago is not None:
        if days_range:
            return None, (dict(
                status='fail',
                message="Either pass `range` or both `start` and `end`, but not both."
            ), 400)
        if start_days_ago < 0 or end_days_ago < 0:
            return None, (dict(
                status='fail',
                message="Start and end must be positive numbers (days ago)."
            ), 400)
        if end_days_ago < start_days_ago:
            return None, (dict(
                status='fail',
                message="Invalid range: `end` must be greater than `start` (end is further back in time)."
            ), 400)
        inactive_since = today - timedelta(days=start_days_ago)
        inactive_until = today - timedelta(days=end_days_ago)
    elif days_range:
        if days_range < 0:
            return None, (dict(
                status='fail',
                message="Range must be a positive number."
            ), 400)
        inactive_since = today - timedelta(days=days_range)
        inactive_until = None
    else:
        return None, (dict(
            status='fail',
            message="Missing required parameters. Provide either `range` or both `start` and `end`."
        ), 400)

    query = User.query.filter(
        cast(User.last_seen, Date) < inactive_since,
        User.verified == True,
    )

    if reminder_since:
        if reminder_since < 0:
            return None, (dict(
                status='fail',
                message="Reminder since must be a positive number."
            ), 400)
        reminder_since_date = today - timedelta(days=reminder_since)
        # Include users who have never been reminded OR were reminded before the grace period date
        query = query.filter(
            or_(
                User.last_reminder_sent.is_(None),
                cast(User.last_reminder_sent, Date) < reminder_since_date,
            )
        )

    if inactive_until:
        query = query.filter(cast(User.last_seen, Date) >= inactive_until)

    if keywords:
        keyword_filter = (
            User.name.ilike(f'%{keywords}%') |
            User.email.ilike(f'%{keywords}%')
        )
        query = query.filter(keyword_filter)

    if disabled_param is not None:
        if str(disabled_param).lower() in ['true', '1', 'yes']:
            query = query.filter(
                or_(User.disabled == True, User.admin_disabled == True)
            )
        elif str(disabled_param).lower() in ['false', '0', 'no']:
            query = query.filter(
                User.disabled == False,
                User.admin_disabled == False
            )

    if created_date_param:
        try:
            created_after_date = datetime.strptime(
                created_date_param, "%Y-%m-%d"
            ).date()
            query = query.filter(
                cast(User.date_created, Date) >= created_after_date,
                cast(User.date_created, Date) <= today
            )
        except ValueError:
            return None, (dict(
                status='fail',
                message="Invalid created date format. Use YYYY-MM-DD."
            ), 400)

    return query, None


def send_inactive_user_reminders_bulk(
    *,
    app=None,
    days_range=None,
    start_days_ago=None,
    end_days_ago=None,
    created_date_param=None,
    keywords=None,
    disabled_param=None,
    reminder_since=30,
    subject="We miss you at Crane Cloud",
    template="user/inactive_user_reminder.html",
):
    """
    Bulk-send inactive user reminder emails and update last_reminder_sent for successful sends.

    Returns: (result_dict, status_code)
    """
    if app is None:
        # When called from a Flask request or Flask CLI (@with_appcontext), use the active app.
        try:
            from flask import current_app
            app = current_app._get_current_object()
        except Exception:
            app = None

    if app is None:
        return dict(
            status="fail",
            message="Flask app context is required to send emails (app is None).",
        ), 500

    query, err = get_inactive_users_query(
        start_days_ago=start_days_ago,
        end_days_ago=end_days_ago,
        days_range=days_range,
        reminder_since=reminder_since,
        keywords=keywords,
        disabled_param=disabled_param,
        created_date_param=created_date_param,
    )
    if err is not None:
        return err

    users = query.all()
    now = datetime.now()
    date_str = now.strftime("%m/%d/%Y")

    successful_ids = []
    errors = []

    for user in users:
        try:
            success = send_inactive_notification_to_user(
                email=user.email,
                name=user.name,
                app=app,
                template=template,
                subject=subject,
                date=date_str,
                is_success_template=True,
            )
            if success:
                successful_ids.append(user.id)
            else:
                errors.append(f"Failed to send email to {user.email}")
        except Exception as exc:
            errors.append(f"Error processing user {user.id}: {exc}")

    try:
        print(f"Successful ids: {successful_ids}")
        # if successful_ids:
        #     db.session.bulk_update_mappings(
        #         User,
        #         [{"id": uid, "last_reminder_sent": now}
        #             for uid in successful_ids],
        #     )
        # db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return dict(status="fail", message=f"Database error: {exc}"), 500

    return dict(
        status="success",
        total_users_processed=len(users),
        emails_sent=len(successful_ids),
        errors=errors if errors else None,
    ), 201


def send_inactive_user_reminders_bulk_cli(
    *,
    days_range=None,
    start_days_ago=None,
    end_days_ago=None,
    created_date_param=None,
    keywords=None,
    disabled_param=None,
    reminder_since=30,
    subject="We miss you at Crane Cloud",
    template="user/inactive_user_reminder.html",
):
    """
    CLI wrapper around send_inactive_user_reminders_bulk 
    """
    result, status = send_inactive_user_reminders_bulk(
        app=None,
        days_range=days_range,
        start_days_ago=start_days_ago,
        end_days_ago=end_days_ago,
        created_date_param=created_date_param,
        keywords=keywords,
        disabled_param=disabled_param,
        reminder_since=reminder_since,
        subject=subject,
        template=template,
    )

    if status >= 400:
        click.echo(f"Error ({status}): {result.get('message')}")
        raise SystemExit(1)

    click.echo(
        f"Processed {result.get('total_users_processed')} users, successfully sent {result.get('emails_sent')} reminder emails."
    )
    if result.get("errors"):
        click.echo("Some errors occurred:")
        for msg in result["errors"]:
            click.echo(f"- {msg}")
