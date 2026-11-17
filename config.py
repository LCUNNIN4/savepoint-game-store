"""Reads database settings from the .env file (or environment variables)."""
import os

from dotenv import load_dotenv

load_dotenv()  # loads variables from a file named ".env" if it exists

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "gamestore"),
}
