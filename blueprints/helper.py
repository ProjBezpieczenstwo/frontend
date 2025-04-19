import requests
from flask import current_app, session


def get_api_base():
    return current_app.config.get("BACKEND_URL")


def get_headers():
    token = session.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_get(endpoint, **kwargs):
    url = f"{get_api_base()}{endpoint}"
    return requests.get(url, headers=get_headers(), **kwargs)


def api_post(endpoint, json=None):
    url = f"{get_api_base()}{endpoint}"
    return requests.post(url, headers=get_headers(), json=json)

def api_delete(endpoint, **kwargs):
    return requests.delete(f"{get_api_base()}{endpoint}", headers=get_headers(), **kwargs)
