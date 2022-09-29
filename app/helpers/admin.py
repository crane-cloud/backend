"""command line utility to create an admin account"""
import re
from app.models.role import Role
from app.models.user import User
from .role_search import has_role


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
        print('password: ', password)
        return
    except Exception as e:
        print(str(e))
        return


def create_default_roles():
    roles = ['administrator', 'customer']
    for role_name in roles:
        role = Role.find_first(name=role_name)
        if not role:
            try:
                role = Role(name=role_name)
                role.save()
            except Exception as e:
                print(str(e))
                return
    print("Roles created successfully")



def is_owner_or_admin(resource, user_id, user_roles):
    is_admin = has_role(user_roles, 'administrator')
    if resource.owner.id:
        is_owner = str(resource.owner.id) == str(user_id)
    else:
        is_owner = False

    return is_admin or is_owner

def is_authorised_project_user(project, user_id, highest_role):
    is_member = False
    user_role = None
    for user_role_item in project.users:
        if str(user_role_item.user_id) == str(user_id):
            is_member = True
            user_role = user_role_item
    if not is_member: 
        return False
    elif highest_role == 'admin' and str(user_role.role) == 'RolesList.admin':
        return True
    elif highest_role == 'member':
        return True
    else:
        return False


def is_current_or_admin(route_user_id, auth_user_id, user_roles):
    is_admin = has_role(user_roles, 'administrator')
    is_current = route_user_id == auth_user_id

    return is_admin or is_current
