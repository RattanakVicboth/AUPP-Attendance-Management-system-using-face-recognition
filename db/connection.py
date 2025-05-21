import os
import pymysql
from dotenv import load_dotenv

# Load variables from .env into environment
load_dotenv()

def get_db_connection():
    return pymysql.connect(
        host     = os.getenv("DB_HOST", "localhost"),
        user     = os.getenv("DB_USER", "root"),
        password = os.getenv("DB_PASS", "Dambo123"),
        db       = os.getenv("DB_NAME", "attendance"),
        cursorclass=pymysql.cursors.DictCursor
    )
