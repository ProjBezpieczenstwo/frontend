import os


class Config:
    BACKEND_URL = os.environ.get("BACKEND_URL", "http://app-server:5000")
    SECRET_KEY = os.environ.get("SECRET_KEY", "that-sucks")
