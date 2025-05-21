import tkinter as tk
from tkinter import Label, Text, Scrollbar, StringVar, Button, Frame, messagebox, ttk
from PIL import Image, ImageTk
from datetime import datetime
import os
import pandas as pd
import pymysql
from db.connection import get_db_connection
from face_scanner import integrate_scanner, setup_face_recognition

# Modern color scheme
BG_COLOR = "#1E1E2E"         # Dark background
LIGHT_COLOR = "#2A2A3C"       # Panel background
PRIMARY_COLOR = "#7B68EE"     # Title/header color
ACCENT_COLOR = "#5D5FEF"      # Button/active elements
TEXT_COLOR = "#F8F8F2"        # Light text
HIGHLIGHT_COLOR = "#FF5555"   # Warning/danger
SUCCESS_COLOR = "#50FA7B"     # Success indicators
LOG_BG = "#282A36"            # Log background
BORDER_COLOR = "#44475A"      # Border highlights

# Initialize global variables
log_messages = []
camera_running = False
scanning_paused = False
cap = None  # Initialize the 'cap' variable for camera

class ModernButton(Button):
    def __init__(self, master=None, **kwargs):
        kwargs.setdefault('relief', 'flat')
        kwargs.setdefault('borderwidth', 0)
        kwargs.setdefault('padx', 15)
        kwargs.setdefault('pady', 8)
        kwargs.setdefault('font', ('Helvetica', 11, 'bold'))
        kwargs.setdefault('fg', "black")
        
        Button.__init__(self, master, **kwargs)
        
        # Bind hover effects
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        
        # Store original bg for leave event
        self.original_bg = kwargs.get('bg', ACCENT_COLOR)
        
    def on_hover(self, event):
        # Brighten the button on hover
        r, g, b = self.winfo_rgb(self.original_bg)
        r = min(65535, int(r * 1.1))
        g = min(65535, int(g * 1.1))
        b = min(65535, int(b * 1.1))
        hover_color = f"#{r//256:02x}{g//256:02x}{b//256:02x}"
        self.config(bg=hover_color)
        
    def on_leave(self, event):
        # Return to original color
        self.config(bg=self.original_bg)

def create_rounded_frame(parent, **kwargs):
    """Create a frame with rounded corners using a canvas background"""
    frame = Frame(parent, **kwargs)
    return frame  # In a real implementation, we would add canvas for rounded corners
    
def back_to_main():
    global camera_running, cap
    # Stop the camera if it's running
    if cap is not None:
        cap.release()
    camera_running = False
    
    # Clear the scanner frame and show the content_frame
    scan_frame.pack_forget()  # Hide the scan frame
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)  # Show the main content frame

    # Force the UI to refresh properly
    window.update_idletasks()  # Update UI before the next change
    window.update()  # Forces the window to refresh and display the main menu

def export_weekly_csv(summary_df, week):
    answer = messagebox.askyesno("Export Confirmation", f"Do you want to export {week} attendance to your Desktop?")
    if answer:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{week.replace(' ', '_')}_Attendance_{timestamp}.csv"
        full_path = os.path.join(desktop_path, filename)
        summary_df.to_csv(full_path, index=False)
        messagebox.showinfo("Exported", f"{filename} has been saved to your Desktop.")
    else:
        messagebox.showinfo("Cancelled", "Export cancelled.")

def show_summary(window, selected_week, profile_data):
    """Show attendance summary for selected week"""
    week = selected_week.get()
    
    # Load or create attendance sheet
    csv_filename = 'AttendanceSheet.csv'
    if not os.path.exists(csv_filename) or os.path.getsize(csv_filename) == 0:
        df = pd.DataFrame(columns=['No', 'ID', 'Name'] + [f"Week {i}" for i in range(1, 14)])
        df.to_csv(csv_filename, index=False)
    else:
        df = pd.read_csv(csv_filename)
    
    # Fill missing IDs and clean names
    for i, row in df.iterrows():
        if pd.isna(row['ID']) or row['ID'] == '':
            name_key = ''.join(c for c in str(row['Name']) if c.isalpha()).lower()
            if name_key in profile_data:
                df.at[i, 'ID'] = profile_data[name_key]['id']
    df.to_csv(csv_filename, index=False)
    
    # Create summary with selected columns
    summary = df[['No', 'ID', 'Name', week]].fillna('')
    
    # Create summary window
    summary_window = tk.Toplevel(window)
    summary_window.title(f"📊 Attendance Summary - {week}")
    summary_window.geometry("700x600")
    summary_window.configure(bg=LIGHT_COLOR)
    
    # Style the window
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview", background=LOG_BG, foreground=TEXT_COLOR, fieldbackground=LOG_BG, font=('Helvetica', 10))
    style.configure("Treeview.Heading", background=PRIMARY_COLOR, foreground=TEXT_COLOR, font=('Helvetica', 11, 'bold'))
    style.map('Treeview', background=[('selected', ACCENT_COLOR)], foreground=[('selected', TEXT_COLOR)])
    
    # Create header
    header_frame = Frame(summary_window, bg=PRIMARY_COLOR)
    header_frame.pack(fill="x")
    
    header_label = Label(header_frame, text=f"Attendance Summary - {week}", 
          font=("Helvetica", 16, "bold"), bg=PRIMARY_COLOR, fg=TEXT_COLOR, pady=15)
    header_label.pack()
    
    # Add statistics
    stats_frame = Frame(summary_window, bg=LIGHT_COLOR)
    stats_frame.pack(fill="x", padx=20, pady=20)
    
    present_count = summary[summary[week] == 'Present'].shape[0]
    total_count = summary.shape[0]
    absent_count = total_count - present_count
    
    # Create a mini dashboard with stats
    stats_container = create_rounded_frame(stats_frame, bg=LIGHT_COLOR, padx=10, pady=10)
    stats_container.pack(fill="x")
    
    # Total students stat
    total_frame = Frame(stats_container, bg=LIGHT_COLOR, padx=10, pady=5)
    total_frame.pack(side="left", expand=True, fill="x")
    Label(total_frame, text="Total Students", font=("Helvetica", 10), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack()
    Label(total_frame, text=f"{total_count}", font=("Helvetica", 18, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack()
    
    # Present stats with percentage
    present_frame = Frame(stats_container, bg=LIGHT_COLOR, padx=10, pady=5)
    present_frame.pack(side="left", expand=True, fill="x")
    Label(present_frame, text="Present", font=("Helvetica", 10), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack()
    Label(present_frame, text=f"{present_count}", font=("Helvetica", 18, "bold"), bg=LIGHT_COLOR, fg=SUCCESS_COLOR).pack()
    present_pct = round((present_count / total_count) * 100) if total_count > 0 else 0
    Label(present_frame, text=f"{present_pct}%", font=("Helvetica", 10), bg=LIGHT_COLOR, fg=SUCCESS_COLOR).pack()
    
    # Absent stats with percentage
    absent_frame = Frame(stats_container, bg=LIGHT_COLOR, padx=10, pady=5)
    absent_frame.pack(side="left", expand=True, fill="x")
    Label(absent_frame, text="Absent", font=("Helvetica", 10), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack()
    Label(absent_frame, text=f"{absent_count}", font=("Helvetica", 18, "bold"), bg=LIGHT_COLOR, fg=HIGHLIGHT_COLOR).pack()
    absent_pct = round((absent_count / total_count) * 100) if total_count > 0 else 0
    Label(absent_frame, text=f"{absent_pct}%", font=("Helvetica", 10), bg=LIGHT_COLOR, fg=HIGHLIGHT_COLOR).pack()
    
    # Create a Treeview widget
    tree_frame = Frame(summary_window, bg=LIGHT_COLOR)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Add scrollbar to the treeview
    tree_scroll = Scrollbar(tree_frame)
    tree_scroll.pack(side="right", fill="y")
    
    tree = ttk.Treeview(tree_frame, columns=("No", "ID", "Name", "Status"), show="headings", yscrollcommand=tree_scroll.set)
    tree.column("No", width=50, anchor="center")
    tree.column("ID", width=120, anchor="center")
    tree.column("Name", width=200)
    tree.column("Status", width=100, anchor="center")
    
    tree.heading("No", text="No")
    tree.heading("ID", text="Student ID")
    tree.heading("Name", text="Name")
    tree.heading("Status", text="Status")
    
    tree.pack(fill="both", expand=True)
    tree_scroll.config(command=tree.yview)
    
    # Insert data
    for _, row in summary.iterrows():
        status = row[week] if row[week] else "Absent"
        tag = "present" if status == "Present" else "absent"
        tree.insert("", "end", values=(row['No'], row['ID'], row['Name'], status), tags=(tag,))
    
    # Configure tags for row colors
    tree.tag_configure("present", background=LOG_BG, foreground=SUCCESS_COLOR)
    tree.tag_configure("absent", background=LOG_BG, foreground=HIGHLIGHT_COLOR)
    
    # Button frame
    button_frame = Frame(summary_window, bg=LIGHT_COLOR, pady=10)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    # Export button
    export_btn = ModernButton(button_frame, text="Export to CSV", 
                            bg=ACCENT_COLOR, fg="black",
                            command=lambda: export_weekly_csv(summary, week))
    export_btn.pack(side="right", padx=10)
    
    # Close button
    close_btn = ModernButton(button_frame, text="Close", 
                       bg=HIGHLIGHT_COLOR, fg="black",
                       command=summary_window.destroy)
    close_btn.pack(side="right", padx=10)

def view_members():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT name, student_id, email, phone FROM users")
        members = cursor.fetchall()

        member_window = tk.Toplevel()
        member_window.title("View Members")
        member_window.geometry("1000x600")
        member_window.configure(bg="#2A2A3C")

        # === Back Button ===
        back_btn = tk.Button(member_window, text="🔙 Back to Dashboard", command=member_window.destroy, 
                             bg="#5D5FEF", fg="black", font=("Helvetica", 12, "bold"))
        back_btn.pack(pady=10)

        # === Treeview table ===
        table_frame = tk.Frame(member_window, bg="#2A2A3C")
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tree_scroll = tk.Scrollbar(table_frame)
        tree_scroll.pack(side="right", fill="y")

        member_table = ttk.Treeview(table_frame, columns=("Name", "Student ID", "Email", "Phone"), 
                                    show="headings", yscrollcommand=tree_scroll.set, height=20)
        tree_scroll.config(command=member_table.yview)

        member_table.column("Name", width=180, anchor="center")
        member_table.column("Student ID", width=120, anchor="center")
        member_table.column("Email", width=200, anchor="center")
        member_table.column("Phone", width=120, anchor="center")

        member_table.heading("Name", text="Name")
        member_table.heading("Student ID", text="Student ID")
        member_table.heading("Email", text="Email")
        member_table.heading("Phone", text="Phone")

        member_table.pack(fill="both", expand=True)

        # Populate the table
        for member in members:
            name = member.get('name', 'N/A')
            student_id = member.get('student_id', 'N/A')
            email = member.get('email', 'N/A')
            phone = member.get('phone', 'N/A')

            member_table.insert("", "end", values=(name, student_id, email, phone))

        # ✅ Function to delete selected members
        def delete_selected_members():
            selected_items = member_table.selection()
            if not selected_items:
                messagebox.showwarning("Warning", "No members selected.")
                return

            confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete {len(selected_items)} selected members?")
            if not confirm:
                return

            try:
                del_connection = get_db_connection()
                del_cursor = del_connection.cursor()

                for item in selected_items:
                    values = member_table.item(item)['values']
                    name_to_delete = values[0]
                    student_id_to_delete = values[1]

                    sql = "DELETE FROM users WHERE name = %s AND student_id = %s"
                    del_cursor.execute(sql, (name_to_delete, student_id_to_delete))
                    member_table.delete(item)  # Delete row from UI immediately

                del_connection.commit()
                del_cursor.close()
                del_connection.close()

                messagebox.showinfo("Success", "Selected members deleted successfully.")

            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete members: {str(e)}")

        # ✅ Delete Button
        delete_btn = tk.Button(member_window, text="🗑️ Delete Selected Members", 
                               bg="#FF5555", fg="black", font=("Helvetica", 12, "bold"),
                               command=delete_selected_members)
        delete_btn.pack(pady=10)

        cursor.close()
        connection.close()

    except Exception as e:
        messagebox.showerror("Error", str(e))


def refresh_dashboard(info_label, profile_data_var, present_var, absent_var, rate_var, selected_week):
    try:
        from face_scanner import setup_face_recognition
        _, _, new_profiles, _ = setup_face_recognition()
        total = len(new_profiles)
        profile_data_var.set(str(total))
        info_label.config(text=f"📁 Students loaded: {total}")
        
        # Update attendance stats
        import pandas as pd
        df = pd.read_csv("AttendanceSheet.csv")
        week = selected_week.get()

        if week not in df.columns or df[week].dropna().eq('').all():
            present = 0
            absent = 0
            rate = 0
        else:
            present = df[df[week] == "Present"].shape[0]
            absent = total - present
            rate = round((present / total) * 100) if total > 0 else 0

        present_var.set(str(present))
        absent_var.set(str(absent))
        rate_var.set(f"{rate}%")

        from tkinter import messagebox
        messagebox.showinfo("Refreshed", "Student data reloaded and dashboard updated.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to refresh: {str(e)}")

def create_main_window():
    """Create the main application window"""
    # Get face recognition data
    _, _, profile_data, _ = setup_face_recognition()
    
    def update_dashboard():
        try:
            df = pd.read_csv("AttendanceSheet.csv")
            week = selected_week.get()

            # Only count if the column exists and has any non-empty values
            if week not in df.columns or df[week].dropna().eq('').all():
                present = 0
                absent = 0
                rate = 0
            else:
                present = df[df[week] == "Present"].shape[0]
                total = len(profile_data)  # Total from image/profile data
                absent = total - present
                rate = round((present / total) * 100) if total > 0 else 0

            present_var.set(str(present))
            absent_var.set(str(absent))
            rate_var.set(f"{rate}%")
        except Exception as e:
            present_var.set("0")
            absent_var.set("0")
            rate_var.set("0%")

    # Create main window
    global window
    window = tk.Tk()
    window.title("🏸 AUPP Attendance System")
    window.geometry("1000x700")
    window.configure(bg=BG_COLOR)
    
    # Style for ttk elements
    # style = ttk.Style()
    # style.theme_use('clam')  # Use clam theme as base
    # style.configure('TButton', background=ACCENT_COLOR, foreground=TEXT_COLOR, borderwidth=0)
    # style.configure('TLabel', background=LIGHT_COLOR, foreground=TEXT_COLOR)
    # style.configure('TFrame', background=LIGHT_COLOR)
    
    # Center window on screen
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')
    
    # Create frames for content and scan screen
    global content_frame, scan_frame
    content_frame = Frame(window, bg=LIGHT_COLOR)
    scan_frame = Frame(window, bg=BG_COLOR)
    
    # Initially show the content frame
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header frame with logo and title
    header_frame = Frame(content_frame, bg=LIGHT_COLOR, pady=10)
    header_frame.pack(fill="x")
    
    # Left side for logo
    logo_frame = Frame(header_frame, bg=LIGHT_COLOR)
    logo_frame.pack(side="left", padx=20)
    
    # Try to load the logo image
    try:
        logo_image = Image.open("static/images/logo.png")
        logo_image = logo_image.resize((80, 80))
        logo_image_tk = ImageTk.PhotoImage(logo_image)
        
        logo_label = Label(logo_frame, image=logo_image_tk, bg=LIGHT_COLOR)
        logo_label.image = logo_image_tk  # Keep a reference
        logo_label.pack()
    except Exception as e:
        print(f"Error loading logo: {e}")
        # Add a text header if image fails
        Label(logo_frame, text="AUPP", font=("Helvetica", 24, "bold"), 
              bg=LIGHT_COLOR, fg=PRIMARY_COLOR).pack(pady=10)
    
    # Right side for title
    title_frame = Frame(header_frame, bg=LIGHT_COLOR)
    title_frame.pack(side="right", expand=True, fill="both")
    
    Label(title_frame, text="AUPP Facial Recognition", 
          font=("Helvetica", 20, "bold"), bg=LIGHT_COLOR, fg=PRIMARY_COLOR).pack(anchor="e", padx=20)
    Label(title_frame, text="Attendance System", 
          font=("Helvetica", 16), bg=LIGHT_COLOR, fg=PRIMARY_COLOR).pack(anchor="e", padx=20)
    
    # Main content area
    main_area = Frame(content_frame, bg=LIGHT_COLOR)
    main_area.pack(fill="both", expand=True, pady=20)
    
    # Left panel - Controls
    left_panel = Frame(main_area, bg=LIGHT_COLOR, width=300)
    left_panel.pack(side="left", fill="y", padx=10)
    left_panel.pack_propagate(False)  # Prevent resizing
    
    # Controls title
    Label(left_panel, text="Dashboard Controls", 
         font=("Helvetica", 14, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(pady=(0, 10))
    
    # Week selection
    selected_week = StringVar(value="Week 1")
    week_headers = [f"Week {i}" for i in range(1, 14)]
    selected_week.trace_add("write", lambda *args: update_dashboard())
    
    week_frame = Frame(left_panel, bg=LIGHT_COLOR, pady=10)
    week_frame.pack(fill="x")
    
    Label(week_frame, text="📅 Select Week", 
          font=("Helvetica", 12), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w")
    
    week_style = ttk.Style()
    week_style.configure('TMenubutton', background=LOG_BG, foreground=TEXT_COLOR, padding=5)
    
    week_menu = ttk.Combobox(week_frame, textvariable=selected_week, values=week_headers, 
                            style='TCombobox', width=15)
    week_menu.pack(fill="x", pady=5)
    
    # Student info display
    info_frame = Frame(left_panel, bg=LOG_BG, pady=10, padx=10)
    info_frame.pack(fill="x", pady=10)
    
    Label(info_frame, text="📊 Statistics", 
         font=("Helvetica", 12, "bold"), bg=LOG_BG, fg=TEXT_COLOR).pack(anchor="w")
    
    Label(info_frame, text=f"📁 Students loaded: {len(profile_data)}", 
         font=("Helvetica", 10), bg=LOG_BG, fg=TEXT_COLOR).pack(anchor="w", pady=5)
    
    # Get the current date
    current_date = datetime.now().strftime("%B %d, %Y")
    Label(info_frame, text=f"📆 Current date: {current_date}", 
         font=("Helvetica", 10), bg=LOG_BG, fg=TEXT_COLOR).pack(anchor="w", pady=5)
    
    # Create a divider
    Frame(left_panel, height=2, bg=BORDER_COLOR).pack(fill="x", pady=15)
    
    # Action buttons
    Label(left_panel, text="Actions", 
         font=("Helvetica", 14, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(pady=(5, 10))
    
    # Function to switch to scanner
    def switch_to_scanner():
        content_frame.pack_forget()
        scan_frame.pack(fill="both", expand=True)
        # Integrate scanner with our UI
        integrate_scanner(window, content_frame, scan_frame, selected_week)
    
    # Start Scanner Button
    ModernButton(left_panel, text="Start Attendance Scanner", bg=ACCENT_COLOR,
                 fg="black", command=switch_to_scanner).pack(fill="x", pady=5)

    ModernButton(left_panel, text="Weekly Summary", bg=PRIMARY_COLOR,
                 fg="black", command=lambda: show_summary(window, selected_week, profile_data)).pack(fill="x", pady=5)

    ModernButton(left_panel, text="View Members", bg=PRIMARY_COLOR,
                 fg="black", command=view_members).pack(fill="x", pady=5)

    ModernButton(left_panel, text="Exit Application", bg=HIGHLIGHT_COLOR,
                 fg="black", command=window.quit).pack(fill="x", pady=5)
   
    # Right panel - Dashboard view
    right_panel = Frame(main_area, bg=LOG_BG, padx=15, pady=15)
    right_panel.pack(side="right", fill="both", expand=True, padx=10)
    
    # Dashboard header
    dash_header = Frame(right_panel, bg=LOG_BG)
    dash_header.pack(fill="x", pady=(0, 10))
    
    Label(dash_header, text="Attendance Dashboard", 
         font=("Helvetica", 16, "bold"), bg=LOG_BG, fg=TEXT_COLOR).pack(side="left")
    
    # Refresh button
    refresh_btn = ModernButton(dash_header, text="Refresh",
                            bg=PRIMARY_COLOR, padx=10, pady=2, fg="black",)
    refresh_btn.pack(side="right")
    
    # Create tabs for different views
    dash_notebook = ttk.Notebook(right_panel)
    dash_notebook.pack(fill="both", expand=True)
    
    # Overview tab
    overview_tab = Frame(dash_notebook, bg=LOG_BG)
    dash_notebook.add(overview_tab, text="Overview")
    
    # Add sample content to Overview tab
    Label(overview_tab, text="Attendance Overview", 
         font=("Helvetica", 14, "bold"), bg=LOG_BG, fg=TEXT_COLOR).pack(pady=10)
    
    # Add cards for key stats
    stats_container = Frame(overview_tab, bg=LOG_BG)
    stats_container.pack(fill="x", pady=10)
    
    present_var = StringVar(value="0")
    absent_var = StringVar(value="0")
    rate_var = StringVar(value="0%")

    def stat_card(parent, title, var, fg_color):
        card = Frame(parent, bg=LIGHT_COLOR, padx=15, pady=10)
        card.pack(side="left", expand=True, fill="both", padx=5)
        Label(card, text=title, font=("Helvetica", 10), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w")
        Label(card, textvariable=var, font=("Helvetica", 24, "bold"), bg=LIGHT_COLOR, fg=fg_color).pack(anchor="center", pady=5)

    stat_card(stats_container, "Total Students", StringVar(value=str(len(profile_data))), TEXT_COLOR)
    stat_card(stats_container, "Present", present_var, SUCCESS_COLOR)
    stat_card(stats_container, "Absent", absent_var, HIGHLIGHT_COLOR)
    stat_card(stats_container, "Attendance Rate", rate_var, ACCENT_COLOR)

    update_dashboard()
    return window

def create_settings_dialog():
    """Create a settings dialog"""
    settings = tk.Toplevel()
    settings.title("Settings")
    settings.geometry("500x400")
    settings.configure(bg=LIGHT_COLOR)
    
    # Create header
    header_frame = Frame(settings, bg=PRIMARY_COLOR)
    header_frame.pack(fill="x")
    Label(header_frame, text="System Settings", 
          font=("Helvetica", 16, "bold"), bg=PRIMARY_COLOR, fg=TEXT_COLOR, pady=10).pack()
    
    # Create notebook for settings categories
    settings_notebook = ttk.Notebook(settings)
    settings_notebook.pack(fill="both", expand=True, padx=20, pady=20)
    
    # General Settings tab
    general_tab = Frame(settings_notebook, bg=LIGHT_COLOR, padx=10, pady=10)
    settings_notebook.add(general_tab, text="General")
    
    # Camera Settings tab
    camera_tab = Frame(settings_notebook, bg=LIGHT_COLOR, padx=10, pady=10)
    settings_notebook.add(camera_tab, text="Camera")
    
    # Database Settings tab
    database_tab = Frame(settings_notebook, bg=LIGHT_COLOR, padx=10, pady=10)
    settings_notebook.add(database_tab, text="Database")
    
    # Export Settings tab
    export_tab = Frame(settings_notebook, bg=LIGHT_COLOR, padx=10, pady=10)
    settings_notebook.add(export_tab, text="Export")
    
    # Add content to General tab
    Label(general_tab, text="Application Settings", 
         font=("Helvetica", 12, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 10))
    
    # Theme selector
    theme_frame = Frame(general_tab, bg=LIGHT_COLOR)
    theme_frame.pack(fill="x", pady=5)
    
    Label(theme_frame, text="Theme:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    theme_var = StringVar(value="Dark")
    theme_menu = ttk.Combobox(theme_frame, textvariable=theme_var, values=["Dark", "Light"], width=15)
    theme_menu.pack(side="left", padx=5)
    
    # Start on system startup
    startup_var = tk.BooleanVar(value=False)
    startup_check = ttk.Checkbutton(general_tab, text="Start application on system startup", 
                                  variable=startup_var)
    startup_check.pack(anchor="w", pady=5)
    
    # Minimize to tray
    tray_var = tk.BooleanVar(value=True)
    tray_check = ttk.Checkbutton(general_tab, text="Minimize to system tray", 
                               variable=tray_var)
    tray_check.pack(anchor="w", pady=5)
    
    # Add content to Camera tab
    Label(camera_tab, text="Camera Settings", 
         font=("Helvetica", 12, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 10))
    
    # Camera selector
    camera_frame = Frame(camera_tab, bg=LIGHT_COLOR)
    camera_frame.pack(fill="x", pady=5)
    
    Label(camera_frame, text="Default Camera:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    camera_var = StringVar(value="0")
    camera_menu = ttk.Combobox(camera_frame, textvariable=camera_var, values=["0", "1", "2"], width=15)
    camera_menu.pack(side="left", padx=5)
    
    # Resolution selector
    resolution_frame = Frame(camera_tab, bg=LIGHT_COLOR)
    resolution_frame.pack(fill="x", pady=5)
    
    Label(resolution_frame, text="Resolution:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    resolution_var = StringVar(value="640x480")
    resolution_menu = ttk.Combobox(resolution_frame, textvariable=resolution_var, 
                                 values=["640x480", "800x600", "1280x720"], width=15)
    resolution_menu.pack(side="left", padx=5)
    
    # Recognition confidence threshold
    confidence_frame = Frame(camera_tab, bg=LIGHT_COLOR)
    confidence_frame.pack(fill="x", pady=5)
    
    Label(confidence_frame, text="Confidence Threshold:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    confidence_var = StringVar(value="0.5")
    confidence_scale = ttk.Scale(confidence_frame, from_=0.1, to=0.9, orient="horizontal", 
                               length=150, value=0.5)
    confidence_scale.pack(side="left", padx=5)
    
    confidence_label = Label(confidence_frame, text="0.5", width=4, 
                           bg=LIGHT_COLOR, fg=TEXT_COLOR)
    confidence_label.pack(side="left", padx=5)
    
    def update_confidence_label(event):
        value = round(confidence_scale.get(), 2)
        confidence_label.config(text=str(value))
        confidence_var.set(str(value))
    
    confidence_scale.bind("<Motion>", update_confidence_label)
    
    # Add content to Database tab
    Label(database_tab, text="Database Settings", 
         font=("Helvetica", 12, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 10))
    
    # Backup settings
    backup_frame = Frame(database_tab, bg=LIGHT_COLOR)
    backup_frame.pack(fill="x", pady=5)
    
    Label(backup_frame, text="Auto Backup:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    backup_var = StringVar(value="Daily")
    backup_menu = ttk.Combobox(backup_frame, textvariable=backup_var, 
                             values=["Daily", "Weekly", "Monthly", "Never"], width=15)
    backup_menu.pack(side="left", padx=5)
    
    # Backup location
    backup_loc_frame = Frame(database_tab, bg=LIGHT_COLOR)
    backup_loc_frame.pack(fill="x", pady=5)
    
    Label(backup_loc_frame, text="Backup Location:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    backup_loc_var = StringVar(value="~/Documents/Backups")
    backup_loc_entry = ttk.Entry(backup_loc_frame, textvariable=backup_loc_var, width=25)
    backup_loc_entry.pack(side="left", padx=5)
    
    backup_browse_btn = ttk.Button(backup_loc_frame, text="Browse...")
    backup_browse_btn.pack(side="left", padx=5)
    
    # Manual backup button
    manual_backup_btn = ModernButton(database_tab, text="Create Backup Now", 
                               bg=ACCENT_COLOR, fg="black")
    manual_backup_btn.pack(anchor="w", pady=10)
    
    # Add content to Export tab
    Label(export_tab, text="Export Settings", 
         font=("Helvetica", 12, "bold"), bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(0, 10))
    
    # Default export format
    format_frame = Frame(export_tab, bg=LIGHT_COLOR)
    format_frame.pack(fill="x", pady=5)
    
    Label(format_frame, text="Default Format:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    format_var = StringVar(value="CSV")
    format_menu = ttk.Combobox(format_frame, textvariable=format_var, 
                             values=["CSV", "Excel", "PDF", "Text"], width=15)
    format_menu.pack(side="left", padx=5)
    
    # Default export location
    export_loc_frame = Frame(export_tab, bg=LIGHT_COLOR)
    export_loc_frame.pack(fill="x", pady=5)
    
    Label(export_loc_frame, text="Export Location:", width=15, anchor="w", 
         bg=LIGHT_COLOR, fg=TEXT_COLOR).pack(side="left")
    
    export_loc_var = StringVar(value="~/Desktop")
    export_loc_entry = ttk.Entry(export_loc_frame, textvariable=export_loc_var, width=25)
    export_loc_entry.pack(side="left", padx=5)
    
    export_browse_btn = ttk.Button(export_loc_frame, text="Browse...")
    export_browse_btn.pack(side="left", padx=5)
    
    # Auto export
    auto_export_var = tk.BooleanVar(value=False)
    auto_export_check = ttk.Checkbutton(export_tab, text="Auto-export attendance report at end of each week", 
                                      variable=auto_export_var)
    auto_export_check.pack(anchor="w", pady=5)
    
    # Bottom buttons
    button_frame = Frame(settings, bg=LIGHT_COLOR)
    button_frame.pack(fill="x", padx=20, pady=10)
    
    save_btn = ModernButton(button_frame, text="Save Settings", 
                          bg=ACCENT_COLOR, fg="black", command=settings.destroy)
    save_btn.pack(side="right", padx=5)
    
    cancel_btn = ModernButton(button_frame, text="Cancel", 
                            bg=HIGHLIGHT_COLOR, fg="black", command=settings.destroy)
    cancel_btn.pack(side="right", padx=5)
    
    return settings

if __name__ == "__main__":
    window = create_main_window()
    window.mainloop()