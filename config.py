import os


class Config:
    BACKEND_URL = os.getenv("backend-uri")
    SECRET_KEY = os.environ.get("SECRET_KEY", "that-sucks")
