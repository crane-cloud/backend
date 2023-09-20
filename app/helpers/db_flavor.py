from types import SimpleNamespace
from app.helpers.activity_logger import log_activity
from app.helpers.database_service import MysqlDbService, PostgresqlDbService
import os

db_flavors = {
    'postgres': {
        'name': 'postgres',
        'image': 'postgres:10.8-alpine',
        'port': 5432
    },
    'mysql': {
        'name': 'mysql',
        'image': 'mysql:8.0',
        'port': 3306
    },
    'mariadb': {
        'name': 'mariadb',
        'image': 'mariadb:10.5',
        'port': 3306
    }
}

# Database flavours
database_flavours = [
    {
        'name': 'mysql',
        'host': os.getenv('ADMIN_MYSQL_HOST'),
        'port': os.getenv('ADMIN_MYSQL_PORT'),
        'class': MysqlDbService()
    },
    {
        'name': 'postgres',
        'host': os.getenv('ADMIN_PSQL_HOST'),
        'port': os.getenv('ADMIN_PSQL_PORT'),
        'class': PostgresqlDbService()
    }
]


def get_db_flavour(flavour_name=None):
    if flavour_name == 'mysql':
        return database_flavours[0]
    elif flavour_name == 'postgres':
        return database_flavours[1]
    else:
        return False


def get_all_db_flavours():
    return database_flavours


def disable_database(database, is_admin=False):
    if database.disabled:
        return SimpleNamespace(
            message="Database is already disabled",
            status_code=409
        )

    # get connection
    db_flavour = get_db_flavour(database.database_flavour_name)
    database_service = db_flavour['class']
    database_connection = database_service.check_db_connection()

    if not database_connection:
        log_activity('Database', status='Failed',
                     operation='Disable',
                     description='Failed to connect to the database service, Internal Server Error',
                     a_project_id=database.project.id,
                     a_db_id=database.id
                     )
        return SimpleNamespace(
            message="Failed to connect to the database service",
            status_code=500
        )

    # Disable the postgres databases
    disable_database = database_service.disable_user_log_in(
        database.user)

    if not disable_database:
        log_activity('Database', status='Failed',
                     operation='Disable',
                     description=f'Unable to disable {database.database_flavour_name} database, Internal Server Error',
                     a_project_id=database.project.id,
                     a_db_id=database.id
                     )

        return SimpleNamespace(
            message="Unable to disable database",
            status_code=500
        )
    try:
        database.disabled = True
        if is_admin:
            database.admin_disabled = True
        database.save()
        log_activity('Database', status='Success',
                     operation='Disable',
                     description=f'Disabled {database.database_flavour_name} database Successfully',
                     a_project_id=database.project.id,
                     a_db_id=database.id)
        return True
    except Exception as err:
        log_activity('Database', status='Failed',
                     operation='Disable',
                     description=err.body,
                     a_project_id=database.project.id,
                     a_db_id=database.id)
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )


def enable_database(database):
    if not database.disabled:
        return SimpleNamespace(
            message="Database is not disabled",
            status_code=409
        )

    # get connection
    db_flavour = get_db_flavour(database.database_flavour_name)
    database_service = db_flavour['class']
    database_connection = database_service.check_db_connection()

    if not database_connection:
        log_activity('Database', status='Failed',
                     operation='Enable',
                     description='Failed to connect to the database service, Internal Server Error',
                     a_project_id=database.project.id,
                     a_db_id=database.id
                     )
        return SimpleNamespace(
            message="Failed to connect to the database service",
            status_code=500
        )

    # Enable the postgres databases
    enable_database = database_service.enable_user_log_in(
        database.user)

    if not enable_database:
        log_activity('Database', status='Failed',
                     operation='Enable',
                     description=f'Unable to enable {database.database_flavour_name} database, Internal Server Error',
                     a_project_id=database.project.id,
                     a_db_id=database.id
                     )

        return SimpleNamespace(
            message="Unable to enable database",
            status_code=500
        )
    try:
        database.disabled = False
        database.admin_disabled = False
        database.save()
        log_activity('Database', status='Success',
                     operation='Enable',
                     description=f'Enabled {database.database_flavour_name} database Successfully',
                     a_project_id=database.project.id,
                     a_db_id=database.id)
        return True
    except Exception as err:
        log_activity('Database', status='Failed',
                     operation='Enable',
                     description=err.body,
                     a_project_id=database.project.id,
                     a_db_id=database.id)
        return SimpleNamespace(
            message=str(err),
            status_code=500
        )
