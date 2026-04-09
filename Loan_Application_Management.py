import customtkinter as ctk
import sqlite3
from tkinter import messagebox, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import hashlib


# -------------------- Database Setup --------------------
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# -------------------- Loan Dashboard --------------------
class LoanDashboard(ctk.CTk):
    def __init__(self, username):
        super().__init__()
        self.title(f"Loan Analytics Dashboard | Welcome {username}")
        self.geometry("1250x750")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.data = None

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=10)
        self.sidebar.pack(side="left", fill="y", padx=10, pady=10)

        title = ctk.CTkLabel(self.sidebar, text="Loan Dashboard",
                             font=("Arial Rounded MT Bold", 18))
        title.pack(pady=(20, 10))

        self.sidebar_btn("Dashboard", self.show_dashboard)
        self.sidebar_btn("Manage Data", self.show_manage_data)
        self.sidebar_btn("Settings", self.show_settings)
        self.sidebar_btn("Logout", self.destroy)

        # Main Frame
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.show_dashboard()

    def sidebar_btn(self, text, command=None):
        btn = ctk.CTkButton(self.sidebar, text=text, font=("Arial", 13),
                            fg_color="#1E88E5", hover_color="#1565C0",
                            corner_radius=20, command=command, width=180)
        btn.pack(pady=8)

    # -------------------- Dashboard --------------------
    def show_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        upload_btn = ctk.CTkButton(self.main_frame, text="Upload Loan Dataset",
                                   command=self.load_dataset,
                                   font=("Arial", 14, "bold"), height=40)
        upload_btn.pack(pady=15)

        self.filter_var = ctk.StringVar(value="All")
        self.filter_dropdown = ctk.CTkOptionMenu(self.main_frame, variable=self.filter_var,
                                                 values=["All"], command=self.apply_filter)
        self.filter_dropdown.pack(pady=10)

        self.cards_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=10)
        self.cards_frame.pack(pady=10)
        self.total_card = self.create_card("Total Loans", "0", "#007ACC")
        self.approved_card = self.create_card("Approved Loans", "0", "#2E7D32")
        self.default_card = self.create_card("Defaults", "0", "#C62828")

        self.chart_frame = ctk.CTkFrame(self.main_frame, corner_radius=10, fg_color="white")
        self.chart_frame.pack(fill="both", expand=True, padx=20, pady=10)

    def create_card(self, title, value, color):
        card = ctk.CTkFrame(self.cards_frame, width=180, height=100, corner_radius=15, fg_color=color)
        card.pack(side="left", padx=15)
        ctk.CTkLabel(card, text=title, text_color="white", font=("Arial", 12, "bold")).pack(pady=(10, 0))
        val = ctk.CTkLabel(card, text=value, text_color="white", font=("Arial", 22, "bold"))
        val.pack()
        return val

    def load_dataset(self):
        path = filedialog.askopenfilename(title="Select Loan Dataset",
                                          filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            self.data = pd.read_csv(path)
            if "Loan_Type" in self.data.columns:
                options = ["All"] + sorted(self.data["Loan_Type"].dropna().unique().tolist())
                self.filter_dropdown.configure(values=options)
            self.update_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def apply_filter(self, selected):
        if self.data is not None:
            if selected == "All":
                filtered = self.data
            else:
                filtered = self.data[self.data["Loan_Type"] == selected]
            self.update_dashboard(filtered)

    def update_dashboard(self, filtered_df=None):
        df = filtered_df if filtered_df is not None else self.data
        if df is None:
            return

        total_loans = len(df)
        approved = len(df[df["Loan_Status"] == "Approved"]) if "Loan_Status" in df.columns else 0
        defaults = df["Default"].sum() if "Default" in df.columns else 0

        self.total_card.configure(text=str(total_loans))
        self.approved_card.configure(text=str(approved))
        self.default_card.configure(text=str(defaults))

        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        fig, axes = plt.subplots(1, 3, figsize=(13, 4))
        fig.patch.set_facecolor("white")

        if "Loan_Status" in df.columns:
            status_counts = df["Loan_Status"].value_counts()
            axes[0].pie(status_counts, labels=status_counts.index, autopct="%1.1f%%",
                        colors=["#2E7D32", "#C62828"])
            axes[0].set_title("Approval vs Rejection")

        if "Loan_Type" in df.columns:
            type_counts = df["Loan_Type"].value_counts()
            axes[1].bar(type_counts.index, type_counts.values, color="#1976D2")
            axes[1].set_title("Loan Distribution by Type")
            axes[1].tick_params(axis='x', rotation=30)

        if "Year" in df.columns and "Default" in df.columns:
            yearly_defaults = df.groupby("Year")["Default"].mean() * 100
            axes[2].plot(yearly_defaults.index, yearly_defaults.values, marker='o', color="#FF9800")
            axes[2].set_title("Default Rate Trends")
            axes[2].set_ylabel("Default Rate (%)")

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # -------------------- Manage Data --------------------
    def show_manage_data(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.main_frame, text="Manage Loan Data",
                             font=("Arial Rounded MT Bold", 18))
        title.pack(pady=15)

        if self.data is None:
            ctk.CTkLabel(self.main_frame, text="No dataset loaded yet!",
                         font=("Arial", 14)).pack(pady=20)
            return

        frame_table = ctk.CTkScrollableFrame(self.main_frame, height=400, width=900)
        frame_table.pack(pady=10)

        columns = list(self.data.columns)
        header = " | ".join(columns)
        ctk.CTkLabel(frame_table, text=header, font=("Consolas", 13, "bold")).pack(anchor="w", padx=10, pady=5)

        for i, row in self.data.head(15).iterrows():
            row_text = " | ".join([str(v) for v in row.values])
            ctk.CTkLabel(frame_table, text=row_text, font=("Consolas", 12)).pack(anchor="w", padx=10)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(btn_frame, text="Add Record", command=self.add_record_popup,
                      fg_color="#2E7D32").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Edit Record", command=self.edit_record_popup,
                      fg_color="#1976D2").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete Record", command=self.delete_record_popup,
                      fg_color="#C62828").pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Save Changes", command=self.save_dataset,
                      fg_color="#6A1B9A").pack(side="left", padx=10)

    def add_record_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Add New Loan Record")
        popup.geometry("400x500")

        entries = {}
        for col in self.data.columns:
            ctk.CTkLabel(popup, text=col).pack()
            e = ctk.CTkEntry(popup)
            e.pack(pady=3)
            entries[col] = e

        def save_new():
            new_data = {col: entries[col].get() for col in self.data.columns}
            self.data = pd.concat([self.data, pd.DataFrame([new_data])], ignore_index=True)
            messagebox.showinfo("Success", "New record added!")
            popup.destroy()
            self.show_manage_data()

        ctk.CTkButton(popup, text="Save", command=save_new).pack(pady=10)

    def edit_record_popup(self):
        if self.data is None or len(self.data) == 0:
            messagebox.showwarning("Warning", "No data available!")
            return

        popup = ctk.CTkToplevel(self)
        popup.title("Edit Record")
        popup.geometry("400x400")

        ctk.CTkLabel(popup, text="Enter Row Index to Edit (0-based):").pack()
        index_entry = ctk.CTkEntry(popup)
        index_entry.pack(pady=5)

        entries = {}

        def load_row():
            try:
                idx = int(index_entry.get())
                row = self.data.iloc[idx]
            except:
                messagebox.showerror("Error", "Invalid index!")
                return

            for col in self.data.columns:
                ctk.CTkLabel(popup, text=col).pack()
                e = ctk.CTkEntry(popup)
                e.insert(0, str(row[col]))
                e.pack(pady=3)
                entries[col] = e

            def save_edit():
                for col in self.data.columns:
                    self.data.at[idx, col] = entries[col].get()
                messagebox.showinfo("Success", "Record updated!")
                popup.destroy()
                self.show_manage_data()

            ctk.CTkButton(popup, text="Save Changes", command=save_edit).pack(pady=10)

        ctk.CTkButton(popup, text="Load Row", command=load_row).pack(pady=10)

    def delete_record_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Delete Record")
        popup.geometry("300x200")

        ctk.CTkLabel(popup, text="Enter Row Index to Delete (0-based):").pack(pady=10)
        index_entry = ctk.CTkEntry(popup)
        index_entry.pack(pady=5)

        def delete_row():
            try:
                idx = int(index_entry.get())
                self.data = self.data.drop(idx).reset_index(drop=True)
                messagebox.showinfo("Deleted", f"Row {idx} deleted successfully!")
                popup.destroy()
                self.show_manage_data()
            except:
                messagebox.showerror("Error", "Invalid index!")

        ctk.CTkButton(popup, text="Delete", command=delete_row, fg_color="#C62828").pack(pady=10)

    def save_dataset(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV Files", "*.csv")])
        if path:
            self.data.to_csv(path, index=False)
            messagebox.showinfo("Success", f"Dataset saved to:\n{path}")

    # -------------------- Settings --------------------
    def show_settings(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(self.main_frame, text="Settings",
                             font=("Arial Rounded MT Bold", 20))
        title.pack(pady=20)

        ctk.CTkLabel(self.main_frame, text="Appearance Mode:", font=("Arial", 14, "bold")).pack(pady=(10, 5))
        appearance_mode = ctk.StringVar(value=ctk.get_appearance_mode())
        ctk.CTkOptionMenu(self.main_frame,
                          variable=appearance_mode,
                          values=["Light", "Dark", "System"],
                          command=lambda mode: ctk.set_appearance_mode(mode)).pack(pady=5)

        ctk.CTkLabel(self.main_frame, text="Color Theme:", font=("Arial", 14, "bold")).pack(pady=(20, 5))
        color_theme = ctk.StringVar(value="blue")
        ctk.CTkOptionMenu(self.main_frame,
                          variable=color_theme,
                          values=["blue", "green", "dark-blue"],
                          command=lambda theme: ctk.set_default_color_theme(theme)).pack(pady=5)

        ctk.CTkLabel(self.main_frame, text="Change Password:", font=("Arial", 14, "bold")).pack(pady=(25, 5))

        old_pass = ctk.CTkEntry(self.main_frame, placeholder_text="Old Password", show="*", width=250)
        old_pass.pack(pady=5)
        new_pass = ctk.CTkEntry(self.main_frame, placeholder_text="New Password", show="*", width=250)
        new_pass.pack(pady=5)

        def change_password():
            from tkinter import simpledialog
            username = simpledialog.askstring("Confirm Username", "Enter your username:")

            if not username or not old_pass.get() or not new_pass.get():
                messagebox.showwarning("Warning", "All fields required!")
                return

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM users WHERE username=?", (username,))
            result = cursor.fetchone()

            if result and result[0] == hash_password(old_pass.get()):
                cursor.execute("UPDATE users SET password=? WHERE username=?",
                               (hash_password(new_pass.get()), username))
                conn.commit()
                messagebox.showinfo("Success", "Password changed successfully!")
            else:
                messagebox.showerror("Error", "Old password incorrect!")
            conn.close()

        ctk.CTkButton(self.main_frame, text="Update Password", command=change_password,
                      fg_color="#1E88E5").pack(pady=10)


# -------------------- Login Window --------------------
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bank Staff Login")
        self.geometry("500x400")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        frame = ctk.CTkFrame(self, corner_radius=15)
        frame.pack(padx=40, pady=40, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="Staff Login", font=("Arial Rounded MT Bold", 20))
        title.pack(pady=15)

        self.username_entry = ctk.CTkEntry(frame, placeholder_text="Username", width=250)
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=250)
        self.password_entry.pack(pady=10)

        ctk.CTkButton(frame, text="Login", command=self.login_user, width=200).pack(pady=10)
        ctk.CTkButton(frame, text="Register", fg_color="gray", command=self.register_user, width=200).pack(pady=5)

    def login_user(self):
        username = self.username_entry.get()
        password = hash_password(self.password_entry.get())

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            messagebox.showinfo("Success", f"Welcome {username}!")
            self.destroy()
            dashboard = LoanDashboard(username)
            dashboard.mainloop()
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    def register_user(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Warning", "All fields required!")
            return

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                           (username, hash_password(password)))
            conn.commit()
            messagebox.showinfo("Success", "User registered successfully!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists!")
        finally:
            conn.close()



if __name__ == "__main__":
    init_db()
    app = LoginApp()
    app.mainloop()
