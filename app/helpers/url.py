import os


def get_app_subdomain(alias):

    DOMAIN = "cranecloud.io"

    if os.getenv("FLASK_ENV") != "production":

        return f'{alias}.dev.{DOMAIN}'

    return f'{alias}.{DOMAIN}'
