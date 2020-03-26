import secrets
import string


def generate_password(password_length):

    characters = string.ascii_letters + string.digits

    password = secrets.choice(string.ascii_lowercase)
    password += secrets.choice(string.ascii_uppercase)

    for i in range(password_length):
        password += secrets.choice(characters)

    return password


def generate_db_uri(hostname, username, password, databasename):

    return f'postgresql+psycopg2://{username}:{password}@{hostname}:5432/{databasename}'
