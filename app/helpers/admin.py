"""command line utility to create an admin account"""
import re
from app.models.role import Role
from app.models.user import User


def create_superuser(email, password, confirm_password):

    email_pattern = re.compile(r"\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?")

    # check passwords match
    if password != confirm_password:
        print("Passwords do not match")
        return

    # check email is of valid format
    if not re.match(email_pattern, email):
        print("Wrong email format")
        return

    # check administrator role exists
    admin_role = Role.find_first(**{'name': 'administrator'})

    if not admin_role:
        try:
            admin_role = Role(name='administrator')
            admin_role.save()
        except Exception as e:
            print(str(e))
            return

    # create admin user
    try:
        admin_user = User.find_first(**{'email': email})
        if admin_user:
            print(f'email {email} already in use')
            return

        admin_user = User(email=email, name='admin', password=password)
        admin_user.verified = True
        admin_user.roles.append(admin_role)
        admin_user.save()
        print("Admin user created successfully")
        return
    except Exception as e:
        print(str(e))
        return
