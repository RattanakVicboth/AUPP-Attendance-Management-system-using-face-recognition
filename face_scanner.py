# face_scanner.py
import cv2
import face_recognition
import os
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from datetime import datetime
from config import path, PRIMARY_COLOR, ACCENT_COLOR, BG_COLOR, TEXT_COLOR, HIGHLIGHT_COLOR, LIGHT_COLOR
import pandas as pd

# Global state
log_messages = []
camera_running = False
scanning_paused = False
cap = None

def setup_face_recognition():
    images, classNames = [], []
    profile_data, student_ids = {}, {}

    os.makedirs('ImagesAttendance', exist_ok=True)
    # os.makedirs('Snapshots', exist_ok=True)

    for cl in os.listdir('ImagesAttendance'):
        if cl.lower().endswith(('.png', '.jpg', '.jpeg')):
            img = cv2.imread(f'ImagesAttendance/{cl}')
            if img is not None:
                images.append(img)
                classNames.append(os.path.splitext(cl)[0])

                filename = os.path.splitext(cl)[0]
                name_part = ''.join(c for c in filename if c.isalpha())
                id_part = ''.join(c for c in filename if c.isdigit())

                if name_part and id_part:
                    profile_data[name_part.lower()] = {
                        "id": id_part,
                        "image": f"ImagesAttendance/{cl}"
                    }
                    student_ids[name_part] = id_part

    valid_encodings, valid_classNames = [], []
    for i, img in enumerate(images):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(rgb)
        if encode:
            valid_encodings.append(encode[0])
            valid_classNames.append(classNames[i])
        else:
            print("Warning: Could not encode a face in one of the images")

    return valid_encodings, valid_classNames, profile_data, student_ids

def integrate_scanner(window, content_frame, scan_frame, selected_week):
    global camera_running, scanning_paused, cap, log_messages
    
    for widget in scan_frame.winfo_children():
        widget.destroy()

    main_container = tk.Frame(scan_frame, bg=LIGHT_COLOR)
    main_container.pack(fill="both", expand=True, padx=20, pady=20)

    left = tk.Frame(main_container, bg=LIGHT_COLOR, padx=15, pady=15, width=400)
    left.pack(side="left", fill="y")

    right = tk.Frame(main_container, bg=LIGHT_COLOR, padx=15, pady=15)
    right.pack(side="right", fill="both", expand=True)

    tk.Label(left, textvariable=selected_week, bg=LIGHT_COLOR, 
             font=("Arial", 12, "bold"), fg=PRIMARY_COLOR).pack(pady=5)

    camera_label = tk.Label(left, width=400, height=300)
    camera_label.pack(pady=10)

    clock_label = tk.Label(left, text="", bg=LIGHT_COLOR, fg=TEXT_COLOR, font=("Arial", 10))
    clock_label.pack()

    tk.Button(left, text="🔙 Back to Main Menu", command=lambda: back_to_main()).pack(pady=15)

    profile_frame = tk.Frame(right, bg=LIGHT_COLOR, padx=20, pady=10)
    profile_frame.pack(fill="x")

    profile_pic = tk.Label(profile_frame, bg=LIGHT_COLOR)
    profile_pic.pack(pady=10)

    name_label = tk.Label(profile_frame, text="Name: ---", bg=LIGHT_COLOR, fg=TEXT_COLOR, font=("Helvetica", 14, "bold"))
    name_label.pack()

    id_label = tk.Label(profile_frame, text="ID: ---", bg=LIGHT_COLOR, fg=TEXT_COLOR, font=("Helvetica", 12))
    id_label.pack()

    status_label = tk.Label(profile_frame, text="Initializing...", bg=LIGHT_COLOR, fg="gray", font=("Helvetica", 12, "bold"))
    status_label.pack(pady=10)

    resume_button = tk.Button(profile_frame, text="✅ Resume Scanning", command=lambda: resume_scanning())

    log_frame = tk.Frame(right, bg=LIGHT_COLOR)
    log_frame.pack(fill="both", expand=True, pady=10)

    tk.Label(log_frame, text="📋 Activity Log", bg=PRIMARY_COLOR, fg="white", font=("Helvetica", 12, "bold")).pack(fill="x")

    log_container = tk.Frame(log_frame, bg=LIGHT_COLOR)
    log_container.pack(fill="both", expand=True)

    log_scrollbar = tk.Scrollbar(log_container)
    log_scrollbar.pack(side="right", fill="y")

    log_text = tk.Text(log_container, height=8, width=50, yscrollcommand=log_scrollbar.set, bg=LIGHT_COLOR, fg=TEXT_COLOR)
    log_text.pack(fill="both", expand=True)
    log_scrollbar.config(command=log_text.yview)

    log_text.insert(tk.END, "🧾 System initializing...\n")
    log_text.see(tk.END)

    try:
        encodeListKnown, classNames, profile_data, student_ids = setup_face_recognition()
        log_text.insert(tk.END, f"✅ Loaded {len(encodeListKnown)} face profiles\n")
    except Exception as e:
        log_text.insert(tk.END, f"❌ Error loading faces: {str(e)}\n")
        encodeListKnown, classNames, profile_data, student_ids = [], [], {}, {}

    def update_log(message):
        print(f"LOG: {message}")
        log_text.insert(tk.END, f"\n{message}\n")
        log_text.see(tk.END)
        log_messages.append(message)

    def update_clock():
        now = datetime.now().strftime('%A %H:%M:%S')
        clock_label.config(text=now)
        if camera_running:
            window.after(1000, update_clock)

    def resume_scanning():
        global scanning_paused
        scanning_paused = False
        resume_button.pack_forget()
        update_log("🔄 Resuming scanning...")

    def back_to_main():
        global camera_running, cap
        camera_running = False
        if cap:
            cap.release()
            cap = None
        scan_frame.pack_forget()
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        window.update_idletasks()
        window.update()

    def mark_attendance(name):
        week = selected_week.get()
        csv_file = 'AttendanceSheet.csv'
        if not os.path.exists(csv_file) or os.path.getsize(csv_file) == 0:
            df = pd.DataFrame(columns=['No', 'ID', 'Name'] + [f"Week {i}" for i in range(1, 14)])
        else:
            df = pd.read_csv(csv_file)
            if 'ID' not in df.columns:
                df.insert(1, 'ID', '')

        name_key = ''.join(c for c in name if c.isalpha()).lower()
        student_id = profile_data.get(name_key, {}).get("id", "Unknown")

        if name in df['Name'].values:
            idx = df[df['Name'] == name].index[0]
            if pd.isna(df.loc[idx, 'ID']) or df.loc[idx, 'ID'] == '':
                df.loc[idx, 'ID'] = student_id
            if pd.isna(df.loc[idx, week]) or df.loc[idx, week] == '':
                df.loc[idx, week] = "Present"
                df.to_csv(csv_file, index=False)
                return f"📝 Marked {name} as Present in {week}"
            return f"⚠️ {name} already marked in {week}"
        else:
            new_row = {col: '' for col in df.columns}
            new_row['No'] = len(df) + 1
            new_row['ID'] = student_id
            new_row['Name'] = name
            new_row[week] = "Present"
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(csv_file, index=False)
            return f"🆕 Added {name} (ID: {student_id}) and marked Present in {week}"

    def update_frame():
        global cap, scanning_paused
        if not camera_running:
            return
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                update_log("❌ Camera not available, retrying...")
                window.after(1000, update_frame)
                return
            update_log("✅ Camera reconnected")

        ret, frame = cap.read()
        if not ret:
            window.after(200, update_frame)
            return

        display_frame = cv2.resize(frame, (400, 300))
        img = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
        img_tk = ImageTk.PhotoImage(image=img)
        camera_label.imgtk = img_tk
        camera_label.configure(image=img_tk)

        if scanning_paused:
            window.after(200, update_frame)
            return

        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        faces = face_recognition.face_locations(rgb_small)

        if faces:
            encodings = face_recognition.face_encodings(rgb_small, faces)
            for encodeFace in encodings:
                if encodeListKnown:
                    faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                    matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
                    matchIndex = np.argmin(faceDis)
                    if matchIndex < len(matches) and matches[matchIndex]:
                        name = classNames[matchIndex]
                        result = mark_attendance(name)
                        update_log(result)
                        name_key = ''.join(c for c in name if c.isalpha()).lower()
                        data = profile_data.get(name_key)
                        if data:
                            name_label.config(text=f"Name: {name_key.capitalize()}")
                            id_label.config(text=f"ID: {data['id']}")
                            status_label.config(text="Present ✓", fg=ACCENT_COLOR)
                            try:
                                img = Image.open(data['image']).resize((140, 140))
                                img_tk = ImageTk.PhotoImage(img)
                                profile_pic.configure(image=img_tk)
                                profile_pic.image = img_tk
                            except Exception as e:
                                update_log(f"🖼️ Error loading image: {str(e)}")
                        scanning_paused = True
                        resume_button.pack(pady=10)
                        update_log("⏸️ Scanning paused. Click Resume to continue.")
                        break

        if camera_running:
            window.after(200, update_frame)

    def start_scanner():
        global camera_running, scanning_paused, cap
        if cap:
            cap.release()
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            update_log("❌ Failed to open camera. Please check permissions.")
            return
        ret, _ = cap.read()
        if not ret:
            update_log("❌ Camera connected but couldn't get image.")
            cap.release()
            return
        update_log("✅ Camera initialized successfully")
        status_label.config(text="Ready", fg="green")
        camera_running = True
        scanning_paused = False
        update_clock()
        update_frame()

    window.after(100, start_scanner)
    return profile_data