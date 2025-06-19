
def has_role(role_list, role_name):
    for role in role_list:
        if role['name'] == role_name:
            return True
    return False


def has_admin_role(role_list):
    for role in role_list:
        if role.name == 'administrator':
            return True
    return False
