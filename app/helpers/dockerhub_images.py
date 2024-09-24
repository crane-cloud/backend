import requests
from types import SimpleNamespace
import re
from app.helpers.activity_logger import log_activity
from app.helpers.crane_app_logger import logger


class ImageCheckError(Exception):
    def __init__(self, message, status_code):
        super().__init__(message)
        self.status_code = status_code


def login_and_get_token(username, password):
    login_url = "https://hub.docker.com/v2/users/login"
    login_data = {
        "username": username,
        "password": password
    }
    try:
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code == 200:
            token = login_response.json().get("token")
            if token:
                return token
            else:
                raise ImageCheckError(
                    message="Login successful, but no token found.",
                    status_code=login_response.status_code,
                )
        else:
            raise ImageCheckError(
                message="Failed to login with provided credentials.",
                status_code=login_response.status_code,
            )
    except requests.RequestException as e:
        raise ImageCheckError(
            message=f"Request error: {str(e)}",
            status_code=None,
        )


def check_image_existence(image_url, password=None):
    match = re.match(r"^(([^/:]+)\/)?([^:]+)(:([^:]+))?$", image_url)

    if not match:
        raise ImageCheckError(
            message="Invalid image format.",
            status_code=500,
        )
    username = match.group(2)
    repository = match.group(3)
    tag = match.group(5) or "latest"

    # Handle public images without username
    if not username:
        username = "library"

    try:
        if password:
            token = login_and_get_token(username, password)
        else:
            token = None  # No token for public images
    except ImageCheckError as e:
        raise e

    url = f"https://hub.docker.com/v2/namespaces/{username}/repositories/{repository}/tags/{tag}"
    print(url)
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        raise ImageCheckError(
            message="Image does not exist.",
            status_code=404,
        )
    else:
        raise ImageCheckError(
            message=f"Error checking image: {response.status_code}",
            status_code=response.status_code,
        )


def docker_image_checker(app_image=None, docker_password=None, project={}):

    try:
        image_url_exists = check_image_existence(
            app_image, docker_password)
    except ImageCheckError as e:
        logger.error(f"Error checking image existence for {app_image}: {e}")
        image_url_exists = False

    if not image_url_exists:
        log_activity('App', status='Failed',
                     operation='Create',
                     description=f'Image url:{app_image} does not exist in docker hub',
                     a_project=project,
                     a_cluster_id=project.cluster_id,
                     a_app=None)
        return f"Image {app_image} does not exist or is private. Make sure you have the right credentials if it is a private image"

    return True
