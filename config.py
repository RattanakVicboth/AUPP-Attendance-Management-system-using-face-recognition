import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# -------------------- File paths --------------------
# Directory for saving attendance photos
path = os.getenv("IMG_DIR", "ImagesAttendance")
# CSV file for attendance records
csv_filename = os.getenv("ATTENDANCE_CSV", "AttendanceSheet.csv")
# Directory for snapshot images
snapshot_folder = os.getenv("SNAPSHOT_FOLDER", "Snapshots")
# Log export file
log_file = os.getenv("LOG_FILE", "log_export.txt")

# -------------------- Theme Colors --------------------
PRIMARY_COLOR      = "#1abc9c"   # Title/header color
ACCENT_COLOR       = "#2ecc71"   # Success/active elements
BG_COLOR           = "#2c3e50"   # Dark background
TEXT_COLOR         = "#ecf0f1"   # Light text
HIGHLIGHT_COLOR    = "#e74c3c"   # Warning/danger
LIGHT_COLOR        = "#34495e"   # Panel background
BUTTON_COLOR       = "#2980b9"   # Primary button background
BUTTON_HOVER_COLOR = "#2573a7"   # Button hover state
LOG_BG             = "#1e272e"   # Log background

# -------------------- Flask Settings --------------------
# Secret key for session management (flash, sessions)
SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-fallback-secret-key")

# -------------------- Database Settings --------------------
# DB_HOST     = os.getenv("DB_HOST", "localhost")
# DB_USER     = os.getenv("DB_USER", "root")
# DB_PASSWORD = os.getenv("DB_PASSWORD", "")
# DB_NAME     = os.getenv("DB_NAME", "aupp_badminton_club")

# -------------------- Mail Settings --------------------
MAIL_SERVER         = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT           = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS        = os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
MAIL_USERNAME       = os.getenv("MAIL_USERNAME", "")
MAIL_PASSWORD       = os.getenv("MAIL_PASSWORD", "")
MAIL_DEFAULT_SENDER = tuple(os.getenv("MAIL_DEFAULT_SENDER", "no-reply@auppcontactform.com").split(",", 1))

