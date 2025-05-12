import os


class Config:
    BACKEND_URL = os.getenv("backend_uri")
    SECRET_KEY = os.environ.get("SECRET_KEY", "9f1c2e4b8d7a6e3f9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e")
