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