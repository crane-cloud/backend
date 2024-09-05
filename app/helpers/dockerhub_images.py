import requests
from types import SimpleNamespace
import re


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
                raise SimpleNamespace(
                    message="Login successful, but no token found.",
                    status_code=login_response.status_code,
                )
        else:
            raise SimpleNamespace(
                message="Failed to login with provided credentials.",
                status_code=login_response.status_code,
            )
    except requests.RequestException as e:
        raise SimpleNamespace(
            message=f"Request error: {str(e)}",
            status_code=None,
        )


def check_image_existence(image_url, password=None):
    match = re.match(r"^(([^/:]+)\/)?([^:]+)(:([^:]+))?$", image_url)

    if not match:
        raise SimpleNamespace(
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
    except SimpleNamespace as e:
        raise e

    url = f"https://hub.docker.com/v2/namespaces/{username}/repositories/{repository}/tags/{tag}"
    headers = {}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        raise SimpleNamespace(
            message="Image does not exist.",
            status_code=404,
        )
    else:
        raise SimpleNamespace(
            message=f"Error checking image: {response.status_code}",
            status_code=response.status_code,
        )
