import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "default_secret_key")
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://app-server:5000")
