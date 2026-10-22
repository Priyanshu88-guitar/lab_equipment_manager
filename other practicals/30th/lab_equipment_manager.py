import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
import os

# --- DATABASE SETUP (3 Tables) ---
def init_db():
    conn = sqlite3.connect('lab_register.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS departments (id INTEGER PRIMARY KEY, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS equipment (id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER, status TEXT, FOREIGN KEY(dept_id) REFERENCES departments(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS maintenance (id INTEGER PRIMARY KEY, equip_id INTEGER, log_date TEXT, FOREIGN KEY(equip_id) REFERENCES equipment(id))''')
    
    # Insert default departments if empty
    c.execute("SELECT COUNT(*) FROM departments")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO departments (name) VALUES (?)", [("Computer Lab",), ("Electronics Lab",), ("Networking Lab",)])
    conn.commit()
    conn.close()

# --- MAIN APP CLASS ---
class LabManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Vibe Coding - Lab Equipment Register")
        self.root.geometry("850x600")
        self.root.configure(bg="#1e1e1e")
        init_db()

        # --- MENU BAR ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export to CSV", command=self.export_csv)
        file_menu.add_command(label="Import from CSV", command=self.import_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Dashboard (View All)", command=lambda: self.switch_frame("Dashboard"))
        nav_menu.add_command(label="Add Equipment", command=lambda: self.switch_frame("Add"))
        nav_menu.add_command(label="Search & Report", command=lambda: self.switch_frame("Search"))
        nav_menu.add_command(label="Data Management", command=lambda: self.switch_frame("Data"))
        menubar.add_cascade(label="Navigate", menu=nav_menu)

        # --- FRAME CONTAINER ---
        self.container = tk.Frame(self.root, bg="#1e1e1e")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in ("Dashboard", "Add", "Search", "Data"):
            frame = tk.Frame(self.container, bg="#1e1e1e")
            self.frames[F] = frame

        self.build_dashboard()
        self.build_add()
        self.build_search()
        self.build_data()
        
        self.switch_frame("Dashboard")

    def switch_frame(self, name):
        for frame in self.frames.values(): frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True)
        if name == "Dashboard": self.load_dashboard_data()

    # --- SCREEN 1: DASHBOARD (Read & Delete) ---
    def build_dashboard(self):
        tk.Label(self.frames["Dashboard"], text="Equipment Dashboard", fg="#00d4ff", bg="#1e1e1e", font=("Helvetica", 16, "bold")).pack(pady=15)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d", borderwidth=0)
        style.configure("Treeview.Heading", background="#333333", foreground="white", font=("Helvetica", 10, "bold"))

        self.tree = ttk.Treeview(self.frames["Dashboard"], columns=("ID", "Name", "Department", "Status"), show="headings", height=15)
        for col in ("ID", "Name", "Department", "Status"): self.tree.heading(col, text=col)
        self.tree.pack(pady=10, padx=20, fill="both", expand=True)
        
        tk.Button(self.frames["Dashboard"], text="Delete Selected", command=self.delete_record, bg="#ef4444", fg="white", font=("Helvetica", 10, "bold"), relief="flat").pack(pady=10)

    def load_dashboard_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        conn = sqlite3.connect('lab_register.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT equipment.id, equipment.name, departments.name, equipment.status 
                          FROM equipment JOIN departments ON equipment.dept_id = departments.id''')
        for row in cursor.fetchall(): self.tree.insert("", tk.END, values=row)
        conn.close()

    def delete_record(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Error", "Select a record to delete.")
            return
        
        # Validation: Confirmation before delete
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete this equipment?"):
            equip_id = self.tree.item(selected, 'values')[0]
            conn = sqlite3.connect('lab_register.db')
            conn.cursor().execute("DELETE FROM equipment WHERE id=?", (equip_id,))
            conn.commit()
            conn.close()
            self.load_dashboard_data()
            messagebox.showinfo("Success", "Record deleted!")

    # --- SCREEN 2: ADD EQUIPMENT (Create) ---
    def build_add(self):
        tk.Label(self.frames["Add"], text="Register New Equipment", fg="#4ade80", bg="#1e1e1e", font=("Helvetica", 16, "bold")).pack(pady=20)
        
        tk.Label(self.frames["Add"], text="Equipment Name:", fg="white", bg="#1e1e1e").pack()
        self.eq_name = tk.Entry(self.frames["Add"], width=40, bg="#2d2d2d", fg="white", insertbackground="white")
        self.eq_name.pack(pady=5)
        
        tk.Label(self.frames["Add"], text="Department ID (1=Comp, 2=Elec, 3=Net):", fg="white", bg="#1e1e1e").pack()
        self.eq_dept = tk.Entry(self.frames["Add"], width=40, bg="#2d2d2d", fg="white", insertbackground="white")
        self.eq_dept.pack(pady=5)

        tk.Label(self.frames["Add"], text="Status (Working/Broken):", fg="white", bg="#1e1e1e").pack()
        self.eq_stat = tk.Entry(self.frames["Add"], width=40, bg="#2d2d2d", fg="white", insertbackground="white")
        self.eq_stat.pack(pady=5)

        tk.Button(self.frames["Add"], text="Save Record", command=self.save_equipment, bg="#4ade80", fg="black", font=("Helvetica", 10, "bold"), relief="flat").pack(pady=20)

    def save_equipment(self):
        name, dept, stat = self.eq_name.get(), self.eq_dept.get(), self.eq_stat.get()
        # Input Validation
        if not name or not dept or not stat:
            messagebox.showerror("Validation Error", "All fields are required!")
            return
            
        conn = sqlite3.connect('lab_register.db')
        conn.cursor().execute("INSERT INTO equipment (name, dept_id, status) VALUES (?, ?, ?)", (name, dept, stat))
        conn.commit()
        conn.close()
        
        self.eq_name.delete(0, tk.END); self.eq_dept.delete(0, tk.END); self.eq_stat.delete(0, tk.END)
        messagebox.showinfo("Success", "Equipment registered successfully!")

    # --- SCREEN 3: SEARCH & REPORT ---
    def build_search(self):
        tk.Label(self.frames["Search"], text="Search & Summary Report", fg="#facc15", bg="#1e1e1e", font=("Helvetica", 16, "bold")).pack(pady=20)
        
        search_frame = tk.Frame(self.frames["Search"], bg="#1e1e1e")
        search_frame.pack(pady=10)
        
        tk.Label(search_frame, text="Search by Status:", fg="white", bg="#1e1e1e").grid(row=0, column=0, padx=5)
        self.search_val = tk.Entry(search_frame, bg="#2d2d2d", fg="white", insertbackground="white")
        self.search_val.grid(row=0, column=1, padx=5)
        tk.Button(search_frame, text="Generate Report", command=self.do_search, bg="#facc15", fg="black", font=("Helvetica", 9, "bold"), relief="flat").grid(row=0, column=2, padx=5)

        self.search_tree = ttk.Treeview(self.frames["Search"], columns=("ID", "Name", "Status"), show="headings", height=10)
        for col in ("ID", "Name", "Status"): self.search_tree.heading(col, text=col)
        self.search_tree.pack(pady=10, padx=20, fill="both", expand=True)

    def do_search(self):
        for row in self.search_tree.get_children(): self.search_tree.delete(row)
        conn = sqlite3.connect('lab_register.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM equipment WHERE status LIKE ?", ('%' + self.search_val.get() + '%',))
        for row in cursor.fetchall(): self.search_tree.insert("", tk.END, values=row)
        conn.close()

    # --- SCREEN 4: DATA IO (Export/Import) ---
    def build_data(self):
        tk.Label(self.frames["Data"], text="Data Import & Export", fg="#00d4ff", bg="#1e1e1e", font=("Helvetica", 16, "bold")).pack(pady=40)
        tk.Button(self.frames["Data"], text="Export Database to CSV", command=self.export_csv, bg="#00d4ff", fg="black", font=("Helvetica", 12, "bold"), relief="flat", width=25, pady=10).pack(pady=10)
        tk.Button(self.frames["Data"], text="Import Data from CSV", command=self.import_csv, bg="#333333", fg="white", font=("Helvetica", 12, "bold"), relief="flat", width=25, pady=10).pack(pady=10)

    def export_csv(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        
        conn = sqlite3.connect('lab_register.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM equipment")
        rows = cursor.fetchall()
        
        with open(filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Name", "Dept_ID", "Status"])
            writer.writerows(rows)
            
        conn.close()
        messagebox.showinfo("Export Success", f"Data exported to {filepath}")

    def import_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath: return
        
        conn = sqlite3.connect('lab_register.db')
        cursor = conn.cursor()
        
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            next(reader) # Skip header
            for row in reader:
                cursor.execute("INSERT INTO equipment (name, dept_id, status) VALUES (?, ?, ?)", (row[1], row[2], row[3]))
                
        conn.commit()
        conn.close()
        self.load_dashboard_data()
        messagebox.showinfo("Import Success", "CSV Data imported into SQLite database!")

if __name__ == "__main__":
    root = tk.Tk()
    app = LabManagerApp(root)
    root.mainloop()