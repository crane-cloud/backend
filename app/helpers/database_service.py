
from mysql.connector import connect, Error
import os
import secrets
import string
from types import SimpleNamespace


class DatabaseService:
    # def __init__(self):
    def create_connection(self):
        try:
            super_connection = connect(
                host=os.getenv('ADMIN_MYSQL_HOST'),
                user=os.getenv('ADMIN_MYSQL_USER'),
                password=os.getenv('ADMIN_MYSQL_PASSWORD'),
                port=os.getenv('ADMIN_MYSQL_PORT', '')
            )
            return super_connection
        except Error as e:
            print(e)
            return False

    def create_db_connection(self, user=None, password=None, db_name=None):
        try:
            user_connection = connect(
                host=os.getenv('ADMIN_MYSQL_HOST'),
                user=user,
                password=password,
                port=os.getenv('ADMIN_MYSQL_PORT', ''),
                database=db_name
            )
            return user_connection
        except Error as e:
            print(e)
            return False

    def check_user_db_rights(self, user=None, password=None, db_name=None):
        try:
            user_connection = self.create_db_connection(
                user=user, password=password, db_name=db_name)
            if not user_connection:
                return False
            return True
        except Error as e:
            print(e)
            return False
        finally:
            if not user_connection:
                return False
            if (user_connection.is_connected()):
                user_connection.close()

    # Create or check user exists database
    def create_database(self, db_name=None, user=None, password=None):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE {db_name}")
            if self.create_user(user=user, password=password):
                cursor.execute(
                    f"GRANT ALL PRIVILEGES ON {db_name}.* To '{user}'")
            return True
        except Error as e:
            print(e)
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    # create database user
    def create_user(self, user=None, password=None):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute(
                f"CREATE USER '{user}' IDENTIFIED BY '{password}' ")
            return True
        except Error as e:
            if e.errno == '1396':
                return True
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    # delete database user
    def delete_user(self, user=None):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute(f"DROP USER '{user}' ")
            return True
        except Error:
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    # delete database
    def delete_database(self, db_name):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {db_name}")
            return True
        except Error:
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    def reset_database(self, db_name=None, user=None, password=None):
        try:
            connection = self.create_connection()
            user_rights = self.check_user_db_rights(
                db_name=db_name, user=user, password=password)
                
            if not connection or not user_rights:
                return False
            cursor = connection.cursor()
            cursor.execute(f"DROP DATABASE {db_name}")
            created_db = self.create_database(
                db_name=db_name, user=user, password=password)
            if not created_db:
                return False
            return True
        except Error:
            return False
        finally:
            if not connection or not user_rights:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    # Show all databases
    def get_all_databases(self):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SHOW DATABASES")
            database_list = []
            for db in cursor:
                database_list.append(db[0].decode())
            return database_list
        except Error:
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    # Show users
    def get_all_users(self):
        try:
            connection = self.create_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            cursor.execute("SELECT user FROM mysql.user GROUP BY user")
            users_list = []
            for db in cursor:
                users_list.append(db[0].decode())
            return users_list
        except Error:
            return False
        finally:
            if not connection:
                return False
            if (connection.is_connected()):
                cursor.close()
                connection.close()


def generate_db_credentials():
    name = ''.join((secrets.choice(string.ascii_letters)
                    for i in range(24)))
    user = ''.join((secrets.choice(string.ascii_letters)
                    for i in range(16)))
    password = ''.join((secrets.choice(
        string.ascii_letters + string.digits + string.punctuation) for i in range(32)))
    return SimpleNamespace(
        user=user,
        name=name,
        password=password
    )

