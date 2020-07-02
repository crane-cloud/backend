

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
