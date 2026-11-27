import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

class Confing:
    SECRET_KEY = os.environ['SECRET_KEY']

    UPLOAD_FOLDER = BASE_DIR / "media" / "videos"

    DB_PAREMS = {
        "host" : os.getenv("DB_HOST", "127.0.0.1"),
        "port" : int(os.getenv("DB_PORT", "5432")),
        "database_name": os.getenv["DB_NAME"],
        "databse_user": os.gerenv["DB_USER"],
        "database_password": os.getenv["DB_PASSWOR"],
    }