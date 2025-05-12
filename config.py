import os


class Config:
    BACKEND_URL = os.getenv("backend_uri")
