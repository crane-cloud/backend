import logging

def has_role(role_list, role_name):
    for role in role_list:
        logging.debug(f"Checking role: {role}")
        if role['name'] == role_name:
            return True
    return False
