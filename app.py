import os
import csv
import subprocess
import sys
import threading
from datetime import datetime
import cv2
import face_recognition
import numpy as np
import pandas as pd
import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from dotenv import load_dotenv
from db.connection import get_db_connection

# Load environment variables
load_dotenv()

# Config
IMG_DIR = os.getenv("IMG_DIR", "ImagesAttendance")
ATTENDANCE_CSV = os.getenv("ATTENDANCE_CSV", "AttendanceSheet.csv")
MEMBERS_CSV = os.getenv("MEMBERS_CSV", "Members.csv")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__, static_folder="static", static_url_path="", template_folder="templates")
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-fallback-secret-key")

# Mail configuration
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes"),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_DEFAULT_SENDER=tuple(os.getenv("MAIL_DEFAULT_SENDER", "AUPP Attendance,no-reply@aupp.edu.kh").split(",", 1))
)
mail = Mail(app)

# Globals
KNOWN_ENCODINGS = []
CLASS_NAMES = []

# Helpers
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_known_faces():
    KNOWN_ENCODINGS.clear()
    CLASS_NAMES.clear()
    os.makedirs(IMG_DIR, exist_ok=True)
    for fname in os.listdir(IMG_DIR):
        if not allowed_file(fname):
            continue
        path = os.path.join(IMG_DIR, fname)
        img = cv2.imread(path)
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)
        if encs:
            KNOWN_ENCODINGS.append(encs[0])
            CLASS_NAMES.append(os.path.splitext(fname)[0])

def ensure_csv(path, header):
    if not os.path.exists(path):
        pd.DataFrame(columns=header).to_csv(path, index=False)

def ensure_data_files():
    weeks = [f"Week {i}" for i in range(1, 14)]
    ensure_csv(ATTENDANCE_CSV, ["Name"] + weeks)
    ensure_csv(MEMBERS_CSV, ["Name", "StudentID", "Email", "Phone", "PhotoFilename"])

def mark_attendance(name, week):
    df = pd.read_csv(ATTENDANCE_CSV)
    now = datetime.now().strftime("%H:%M:%S")
    if name in df["Name"].values:
        idx = df.index[df["Name"] == name][0]
        if pd.isna(df.at[idx, week]) or df.at[idx, week] == "":
            df.at[idx, week] = now
            df.to_csv(ATTENDANCE_CSV, index=False)
            return {"new": False, "time": now}
        return {"already": True}
    row = {c: "" for c in df.columns}
    row["Name"], row[week] = name, now
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(ATTENDANCE_CSV, index=False)
    return {"new": True, "time": now}

def delete_attendance(name):
    df = pd.read_csv(ATTENDANCE_CSV)
    if name in df["Name"].values:
        df = df[df["Name"] != name]
        df.to_csv(ATTENDANCE_CSV, index=False)
        return True
    return False

# Page Routes
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/membership")
def membership():
    return render_template("membership.html")

@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/verify_admin", methods=["POST"])
def verify_admin():
    data = request.get_json() or {}
    username = data.get('username','').strip()
    password = data.get('password','').strip()
    admin_file = 'admin_account.txt'
    if os.path.exists(admin_file):
        with open(admin_file,'r',encoding='utf-8') as f:
            for line in f:
                u,p = (x.strip() for x in line.split(',',1))
                if username==u and password==p:
                    return jsonify({'status':'success'})
    return jsonify({'status':'fail'})

@app.route("/api/register", methods=["POST"])
def api_register():
    name = request.form.get("name", "").strip()
    student_id = request.form.get("student_id", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    photo = request.files.get("photo")

    if not all([name, student_id, email, phone, photo]):
        return jsonify(error="Missing fields"), 400

    errors = {}
    if not re.match(r'^[a-zA-Z\s]+$', name): errors['name'] = 'Letters/spaces only'
    if not re.match(r'^[0-9]{1,8}$', student_id): errors['student_id'] = 'Up to 8 digits'
    if not re.match(r'^[A-Za-z0-9._%+-]+@aupp\.edu\.kh$', email): errors['email'] = 'Invalid AUPP email'
    if not re.match(r'^[0-9]{8,9}$', phone): errors['phone'] = '8-9 digits'
    if photo and not allowed_file(photo.filename): errors['photo'] = 'Invalid file type'
    if errors: return jsonify(error="Validation failed", details=errors), 400

    os.makedirs(IMG_DIR, exist_ok=True)
    _, ext = os.path.splitext(photo.filename)
    safe = secure_filename(name.replace(" ", ""))
    filename = f"{safe}{student_id}{ext}"

    buf = np.frombuffer(photo.read(), np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(error="Invalid image"), 400
    encs = face_recognition.face_encodings(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    if not encs:
        return jsonify(error="No face detected"), 400

    photo.stream.seek(0)
    photo.save(os.path.join(IMG_DIR, filename))

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO users (name, student_id, email, phone, photo) VALUES (%s,%s,%s,%s,%s)",
                        (name, student_id, email, phone, filename))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify(error=f"DB error: {e}"), 500
    finally:
        conn.close()

    KNOWN_ENCODINGS.append(encs[0])
    CLASS_NAMES.append(f"{safe}{student_id}")
    return jsonify(message="Registration successful"), 200

@app.route("/api/check_face", methods=["POST"])
def api_check_face():
    photo = request.files.get("photo")
    if not photo:
        return jsonify(error="No photo uploaded"), 400
    buf = np.frombuffer(photo.read(), np.uint8)
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(error="Invalid image"), 400
    encs = face_recognition.face_encodings(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return jsonify(face_detected=bool(encs))

@app.route("/api/mark", methods=["POST"])
def api_mark():
    if 'file' not in request.files or 'week' not in request.form:
        return jsonify(error="Missing file/week"), 400
    week = request.form['week']
    data = np.frombuffer(request.files['file'].read(), np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    encs = face_recognition.face_encodings(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
    for f in encs:
        d = face_recognition.face_distance(KNOWN_ENCODINGS, f)
        if len(d) == 0:
            continue
        i = np.argmin(d)
        if face_recognition.compare_faces([KNOWN_ENCODINGS[i]], f)[0]:
            return jsonify(name=CLASS_NAMES[i], result=mark_attendance(CLASS_NAMES[i], week))
    return jsonify(name=None, error="No match"), 200

@app.route("/api/delete", methods=['POST'])
def api_delete():
    name = (request.get_json() or {}).get('name')
    if not name:
        return jsonify(error="No name"), 400
    return jsonify(deleted=delete_attendance(name))

@app.route('/send_message', methods=['POST'])
def send_message():
    name = request.form['name'].strip()
    email = request.form['email'].strip()
    phone = request.form['phone'].strip()
    text = request.form['message'].strip()

    body = f"""You have a new message from the AUPP Attendance System Contact Form:\n\nName: {name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{text}"""

    recipient = os.getenv('CONTACT_RECIP', '2022133heng@aupp.edu.kh')
    msg = Message(subject=f"AUPP Contact: {name}", recipients=[recipient], body=body)
    try:
        mail.send(msg)
        flash("Your message has been sent!", "success")
    except Exception as e:
        app.logger.error("Mail send error: %s", e)
        flash("Sorry, we couldn't send your message. Please try again later.", "danger")
    return redirect(url_for('faq'))

@app.route("/start-scan")
def start_scan():
    def run():
        subprocess.Popen([sys.executable, os.path.join(os.path.dirname(__file__), "main.py")])
    threading.Thread(target=run).start()
    return "Launching scanner"

if __name__ == "__main__":
    os.makedirs(IMG_DIR, exist_ok=True)
    load_known_faces()
    ensure_data_files()
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES LIKE 'users'")
        if not cur.fetchone():
            cur.execute("""
            CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                student_id VARCHAR(20) NOT NULL,
                email VARCHAR(100) NOT NULL,
                phone VARCHAR(20) NOT NULL,
                photo VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            conn.commit()
    conn.close()
    app.run(debug=True)
