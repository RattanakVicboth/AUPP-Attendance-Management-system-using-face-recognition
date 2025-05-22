#  AUPP Attendance Management System Using Face Recognition

A facial recognition-based attendance system for the AUPP Attendance Management System Using Face Recognition. Built with Flask, OpenCV, MySQL, and Face Recognition libraries, this web-based app allows students to register with a photo and log attendance seamlessly through facial scanning.

## 📦 Features

* ✅ **Student Registration** with photo (Name + Student ID stored as filename)
* 🤳 **Facial Recognition** attendance system
* 📄 **CSV & MySQL Database** support for attendance tracking and member info
* 📧 **Contact Form** with email integration
* 🔐 **Admin Verification** with optional clear/reset data functionality
* 🌐 **Responsive Frontend** with styled pages (`home`, `membership`, `register`, `FAQ`)
* 🖥️ **Tkinter GUI Scanner** for offline attendance logging

## 🚀 Technologies Used

* **Backend**: Python, Flask, Flask-Mail, Flask-CORS, MySQL
* **Face Recognition**: OpenCV, `face_recognition`
* **Frontend**: HTML, CSS, JavaScript
* **Other**: `.env` for secrets, threading for scanner

## ⚙️ Setup Instructions

### 1. **Clone the repository**

```bash
git clone https://github.com/RattanakVicboth/AUPP-Attendance-Management-system-using-face-recognition.git
cd attendance-system
```

### 2. **Create a virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 3. **Set up `.env` file**

Create a `.env` file with:

```env
FLASK_SECRET_KEY=your_secret_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_app_password
CONTACT_RECIP=your_contact_recipient@gmail.com
```

### 4. **Run the app**

```bash
python app.py
```

### 5. **Launch the facial scanner**

```bash
python main.py
```

## 🧪 Face Recognition Setup

This project uses [`face_recognition`](https://github.com/ageitgey/face_recognition). You may need to install dependencies like `dlib`. On Windows, try:

```bash
pip install cmake
pip install dlib
pip install face_recognition
```

## 🔒 Admin Login

Admin credentials are stored in `admin_account.txt` as:

```
admin_username,admin_password
```

## 📬 Contact Form
Messages from the FAQ contact form are sent via Gmail SMTP. Ensure:
* You’ve enabled [App Passwords](https://myaccount.google.com/apppasswords)
* Less secure app access is enabled (if not using App Passwords)
