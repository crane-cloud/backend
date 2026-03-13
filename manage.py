import click

from flask.cli import with_appcontext

from app.helpers.admin import create_superuser, create_default_roles
from app.helpers.registry import add_registries
from app.helpers.user_finder import send_inactive_user_reminders_bulk_cli


@click.command('admin_user', help='Create an admin user')
@click.option('-e', '--email', prompt=True, help='admin email')
@click.option('-p', '--password', prompt=True, help='admin password')
@click.option('-c', '--confirm_password', prompt=True, help='confirm_password')
@with_appcontext
def admin_user(email, password, confirm_password):
    create_superuser(email, password, confirm_password)


@click.command('create_roles', help='Create default user roles')
@with_appcontext
def create_roles():
    create_default_roles()


@click.command('create_registries', help='Creates registries')
@with_appcontext
def create_registries():
    add_registries()


@click.command(
    'send_inactive_user_reminders', help='Send reminder emails to inactive users in bulk',
)
@click.option(
    '-r',
    '--reminder-since',
    type=int,
    default=30,
    show_default=True,
    help='Only send to users whose last reminder (if any) was sent more than N days ago.',
)
@click.option(
    '--range',
    'days_range',
    type=int,
    default=360,
    show_default=True,
    help='Send to users last seen more than N days ago. Incompatible with --start/--end.',
)
@with_appcontext
def send_inactive_user_reminders(
    reminder_since,
    days_range,
):
    send_inactive_user_reminders_bulk_cli(
        days_range=days_range,
        reminder_since=reminder_since,
    )
