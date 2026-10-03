import os
import io
import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from cryptography.fernet import Fernet

# ----------------------------------------------------------------------
# 1. ENCRYPTION & DATABASE MANAGER
# ----------------------------------------------------------------------


class DatabaseManager:
    def __init__(self, db_name="school_records.db", key_file="secret.key"):
        self.db_name = db_name
        self.key_file = key_file
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)
        self._init_db()

    def _load_or_generate_key(self):
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
        with open(self.key_file, "rb") as f:
            return f.read()

    def encrypt(self, text: str) -> str:
        if not text:
            return ""
        return self.cipher.encrypt(text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return ""
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except Exception:
            return "[Decryption Error]"

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    grade TEXT,
                    parent_username TEXT,
                    enc_medical_notes TEXT,
                    enc_personal_address TEXT,
                    photo_data BLOB
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Management')"
                )
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES ('teacher1', 'teacher123', 'Teacher')"
                )
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES ('parent1', 'parent123', 'Parent')"
                )

            conn.commit()

    def add_student(self, name, grade, parent_user, medical_notes, address, photo_bytes):
        enc_med = self.encrypt(medical_notes)
        enc_addr = self.encrypt(address)
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (name, grade, parent_username, enc_medical_notes, enc_personal_address, photo_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, grade, parent_user, enc_med, enc_addr, photo_bytes))
            conn.commit()

    def get_students_for_role(self, role, username):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if role == "Management":
                cursor.execute(
                    "SELECT id, name, grade, parent_username, enc_medical_notes, enc_personal_address, photo_data FROM students"
                )
            elif role == "Teacher":
                cursor.execute(
                    "SELECT id, name, grade, parent_username, enc_medical_notes, enc_personal_address, photo_data FROM students"
                )
            elif role == "Parent":
                cursor.execute(
                    "SELECT id, name, grade, parent_username, enc_medical_notes, enc_personal_address, photo_data FROM students WHERE parent_username=?",
                    (username,)
                )
            else:
                return []
            return cursor.fetchall()

    def authenticate(self, username, password):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM users WHERE username=? AND password=?",
                (username, password),
            )
            row = cursor.fetchone()
            return row[0] if row else None


# ----------------------------------------------------------------------
# 2. THEME DEFINITIONS
# ----------------------------------------------------------------------
THEMES = {
    "Navy Dark": {
        "bg": "#0f172a",
        "card_bg": "#1e293b",
        "fg": "#f8fafc",
        "accent": "#38bdf8",
        "button_fg": "#0f172a",
        "field_bg": "#334155"
    },
    "Emerald Light": {
        "bg": "#f0fdf4",
        "card_bg": "#ffffff",
        "fg": "#166534",
        "accent": "#15803d",
        "button_fg": "#ffffff",
        "field_bg": "#dcfce7"
    },
    "Modern Purple": {
        "bg": "#2e1065",
        "card_bg": "#3b0764",
        "fg": "#f3e8ff",
        "accent": "#a855f7",
        "button_fg": "#ffffff",
        "field_bg": "#581c87"
    }
}


# ----------------------------------------------------------------------
# 3. MAIN GUI APPLICATION
# ----------------------------------------------------------------------
class SchoolRecordsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Christ College School Register - School Records Management System")
        self.geometry("950x650")

        self.db = DatabaseManager()
        self.current_theme = "Navy Dark"
        self.current_user = None
        self.current_role = None
        self.selected_photo_bytes = None

        self._apply_global_styles()
        self.show_login_screen()

    def _apply_global_styles(self):
        theme = THEMES[self.current_theme]
        self.configure(bg=theme["bg"])
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=theme["bg"])
        style.configure("Card.TFrame", background=theme["card_bg"], relief="flat")
        style.configure(
            "TLabel",
            background=theme["card_bg"],
            foreground=theme["fg"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Header.TLabel",
            font=("Segoe UI", 16, "bold"),
            background=theme["card_bg"],
            foreground=theme["accent"],
        )
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 22, "bold"),
            background=theme["bg"],
            foreground=theme["accent"],
        )

        style.configure(
            "TButton",
            font=("Segoe UI", 10, "bold"),
            background=theme["accent"],
            foreground=theme["button_fg"],
            borderwidth=0,
        )
        style.map(
            "TButton",
            background=[("active", theme["fg"])],
            foreground=[("active", theme["bg"])],
        )

        style.configure(
            "Treeview",
            background=theme["card_bg"],
            foreground=theme["fg"],
            fieldbackground=theme["card_bg"],
            font=("Segoe UI", 10),
            rowheight=28,
        )
        style.configure(
            "Treeview.Heading",
            background=theme["field_bg"],
            foreground=theme["fg"],
            font=("Segoe UI", 10, "bold"),
        )

    def change_theme(self, theme_name):
        self.current_theme = theme_name
        self._apply_global_styles()
        if self.current_user:
            self.show_dashboard()

    # ------------------------------------------------------------------
    # SCREEN 1: LOGIN
    # ------------------------------------------------------------------
    def show_login_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        theme = THEMES[self.current_theme]

        header = ttk.Label(
            self, text="🎓 Christ College School Register", style="Title.TLabel"
        )
        header.pack(pady=(60, 20))

        card = ttk.Frame(self, style="Card.TFrame", padding=30)
        card.pack(ipadx=20, ipady=20)

        ttk.Label(card, text="Portal Login", style="Header.TLabel").grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )

        ttk.Label(card, text="Username:").grid(row=1, column=0, sticky="e", pady=8, padx=5)
        username_entry = ttk.Entry(card, width=25)
        username_entry.grid(row=1, column=1, pady=8, padx=5)

        ttk.Label(card, text="Password:").grid(row=2, column=0, sticky="e", pady=8, padx=5)
        password_entry = ttk.Entry(card, show="•", width=25)
        password_entry.grid(row=2, column=1, pady=8, padx=5)

        def handle_login():
            u = username_entry.get().strip()
            p = password_entry.get().strip()
            role = self.db.authenticate(u, p)
            if role:
                self.current_user = u
                self.current_role = role
                self.show_dashboard()
            else:
                messagebox.showerror("Access Denied", "Invalid username or password.")

        login_btn = ttk.Button(card, text="Sign In", command=handle_login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=(20, 0), sticky="ew")

        # Allow Enter key to submit
        password_entry.bind("<Return>", lambda event: handle_login())
        username_entry.bind("<Return>", lambda event: handle_login())

        theme_frame = ttk.Frame(self)
        theme_frame.pack(pady=30)
        ttk.Label(theme_frame, text="Theme:", background=theme["bg"], foreground=theme["fg"]).pack(
            side="left", padx=5
        )
        theme_box = ttk.Combobox(theme_frame, values=list(THEMES.keys()), state="readonly", width=15)
        theme_box.set(self.current_theme)
        theme_box.pack(side="left")
        theme_box.bind("<<ComboboxSelected>>", lambda e: self.change_theme(theme_box.get()))

    # ------------------------------------------------------------------
    # SCREEN 2: DASHBOARD
    # ------------------------------------------------------------------
    def show_dashboard(self):
        for widget in self.winfo_children():
            widget.destroy()

        top_bar = ttk.Frame(self, style="Card.TFrame", padding=10)
        top_bar.pack(fill="x", side="top")

        user_info = f"Logged in as: {self.current_user} ({self.current_role})"
        ttk.Label(top_bar, text=user_info, font=("Segoe UI", 11, "bold")).pack(side="left", padx=10)

        logout_btn = ttk.Button(top_bar, text="Logout", command=self.show_login_screen)
        logout_btn.pack(side="right", padx=10)

        theme_box = ttk.Combobox(top_bar, values=list(THEMES.keys()), state="readonly", width=15)
        theme_box.set(self.current_theme)
        theme_box.pack(side="right", padx=10)
        theme_box.bind("<<ComboboxSelected>>", lambda e: self.change_theme(theme_box.get()))

        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)

        # Left Column: Records Table
        table_frame = ttk.Frame(container, style="Card.TFrame", padding=15)
        table_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(table_frame, text="Student Records", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        columns = ("ID", "Name", "Grade", "Parent Account", "Medical Notes")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_student_select)

        # Right Column: Record Entry / Details Display
        self.detail_frame = ttk.Frame(container, style="Card.TFrame", padding=15)
        self.detail_frame.pack(side="right", fill="both", expand=False, width=320)

        self._render_side_panel()
        self._load_table_data()

    def _render_side_panel(self):
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        if self.current_role in ["Management", "Teacher"]:
            ttk.Label(self.detail_frame, text="Add New Student", style="Header.TLabel").pack(
                anchor="w", pady=(0, 10)
            )

            ttk.Label(self.detail_frame, text="Full Name:").pack(anchor="w", pady=(5, 0))
            self.ent_name = ttk.Entry(self.detail_frame)
            self.ent_name.pack(fill="x", pady=(0, 5))

            ttk.Label(self.detail_frame, text="Grade/Class:").pack(anchor="w", pady=(5, 0))
            self.ent_grade = ttk.Entry(self.detail_frame)
            self.ent_grade.pack(fill="x", pady=(0, 5))

            ttk.Label(self.detail_frame, text="Parent Username:").pack(anchor="w", pady=(5, 0))
            self.ent_parent = ttk.Entry(self.detail_frame)
            self.ent_parent.pack(fill="x", pady=(0, 5))

            ttk.Label(self.detail_frame, text="Medical Notes (Encrypted):").pack(anchor="w", pady=(5, 0))
            self.ent_med = ttk.Entry(self.detail_frame)
            self.ent_med.pack(fill="x", pady=(0, 5))

            ttk.Label(self.detail_frame, text="Personal Address (Encrypted):").pack(anchor="w", pady=(5, 0))
            self.ent_addr = ttk.Entry(self.detail_frame)
            self.ent_addr.pack(fill="x", pady=(0, 5))

            img_btn = ttk.Button(self.detail_frame, text="Upload Photo", command=self._select_image)
            img_btn.pack(fill="x", pady=10)

            self.lbl_img_preview = ttk.Label(self.detail_frame, text="[No Photo Selected]")
            self.lbl_img_preview.pack(pady=5)

            save_btn = ttk.Button(
                self.detail_frame,
                text="Save Student Record",
                command=self._save_student,
            )
            save_btn.pack(fill="x", pady=(10, 0))
        else:
            ttk.Label(self.detail_frame, text="Student Photo", style="Header.TLabel").pack(
                anchor="w", pady=(0, 10)
            )
            self.lbl_img_preview = ttk.Label(self.detail_frame, text="Select a record to view details.")
            self.lbl_img_preview.pack(pady=20)

    def _select_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        if path:
            with open(path, "rb") as f:
                self.selected_photo_bytes = f.read()
            self.lbl_img_preview.config(text=f"Selected: {os.path.basename(path)}")

    def _save_student(self):
        name = self.ent_name.get().strip()
        grade = self.ent_grade.get().strip()
        parent = self.ent_parent.get().strip()
        med = self.ent_med.get().strip()
        addr = self.ent_addr.get().strip()

        if not name or not grade:
            messagebox.showwarning("Validation Error", "Name and Grade are required.")
            return

        self.db.add_student(name, grade, parent, med, addr, self.selected_photo_bytes)
        messagebox.showinfo("Success", "Student record successfully saved!")

        self.ent_name.delete(0, tk.END)
        self.ent_grade.delete(0, tk.END)
        self.ent_parent.delete(0, tk.END)
        self.ent_med.delete(0, tk.END)
        self.ent_addr.delete(0, tk.END)
        self.selected_photo_bytes = None
        self._render_side_panel()
        self._load_table_data()

    def _load_table_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        rows = self.db.get_students_for_role(self.current_role, self.current_user)
        for row in rows:
            sid, name, grade, parent, enc_med, enc_addr, photo_data = row

            if self.current_role == "Management":
                med_display = self.db.decrypt(enc_med)
            elif self.current_role == "Parent":
                med_display = self.db.decrypt(enc_med)
            else:
                med_display = "🔒 Restricted (Admin Only)"

            self.tree.insert("", "end", iid=sid, values=(sid, name, grade, parent, med_display))

    def _on_student_select(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        sid = selected_item[0]
        rows = self.db.get_students_for_role(self.current_role, self.current_user)
        selected_row = next((r for r in rows if str(r[0]) == str(sid)), None)

        if selected_row and selected_row[6]:  # photo_data
            photo_bytes = selected_row[6]
            image = Image.open(io.BytesIO(photo_bytes))
            image.thumbnail((180, 180))
            photo = ImageTk.PhotoImage(image)
            self.lbl_img_preview.config(image=photo, text="")
            self.lbl_img_preview.image = photo
        else:
            self.lbl_img_preview.config(image="", text="[No Photo Available]")


if __name__ == "__main__":
    app = SchoolRecordsApp()
    app.mainloop()