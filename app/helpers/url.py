
from app.helpers.alias import shorten_alias


def get_app_subdomain(alias, domain):
    return f'{shorten_alias(alias)}.{domain}'
