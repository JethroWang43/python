import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database setup
def init_db():
    with sqlite3.connect("budget_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS summaries (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            title TEXT,
                            date TEXT,
                            time TEXT,
                            budget REAL,
                            total_spent REAL,
                            remaining REAL,
                            categories TEXT,
                            description TEXT)''')
        conn.commit()

# Insert sample data with predefined dates
def insert_sample_data():
    with sqlite3.connect("budget_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM summaries")
        if cursor.fetchone()[0] == 0:  
            sample_data = [
                ("Groceries", "2025-03-23", "08:30", 5000, 1000, 4000, "Food:500, Essentials:500", "Morning groceries"),
                ("Groceries", "2025-03-23", "15:00", 5000, 2000, 2000, "Food:1500, Essentials:500", "Afternoon shopping"),
                ("Entertainment", "2025-03-21", "19:30", 2000, 800, 1200, "Movies:500, Games:300", "Weekend fun"),
                ("Utilities", "2025-03-20", "10:00", 3000, 1500, 1500, "Electricity:1000, Water:500", "Monthly bills"),
                ("Rent", "2025-03-01", "09:00", 10000, 10000, 0, "Apartment:10000", "Monthly rent payment")
            ]
            cursor.executemany("INSERT INTO summaries (title, date, time, budget, total_spent, remaining, categories, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", sample_data)
            conn.commit()

# Load data into table, sorted by date & time
def load_data(search_query=""):
    for row in tree.get_children():
        tree.delete(row)

    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    
    query = "SELECT title, date, time, budget, total_spent, remaining, description FROM summaries ORDER BY date DESC, time DESC"
    params = ()
    
    if search_query:
        query = "SELECT title, date, time, budget, total_spent, remaining, description FROM summaries WHERE title LIKE ? ORDER BY date DESC, time DESC"
        params = (f"%{search_query}%",)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    for row in rows:
        tree.insert("", "end", values=row)

# Show pie chart for selected entry
def show_pie_chart_for_selection(event):
    selected_item = tree.selection()
    if not selected_item:
        return
    
    item = tree.item(selected_item)
    title, date, time = item['values'][0], item['values'][1], item['values'][2]

    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT budget, remaining, categories, description FROM summaries WHERE title = ? AND date = ? AND time = ?", (title, date, time))
    data = cursor.fetchone()
    conn.close()

    if not data:
        return

    budget, remaining, categories_data, description = data
    categories = categories_data.split(',')

    try:
        category_totals = {name.strip(): float(value) for name, value in (cat.split(':') for cat in categories)}
    except ValueError:
        messagebox.showerror("Error", "Invalid category format in database.")
        return

    details_window = tk.Toplevel(root)
    details_window.title(f"Budget Details - {title} ({date} {time})")
    details_window.configure(bg="#6200EA")

    info_frame = tk.Frame(details_window, bg="#D1C4E9")
    info_frame.pack(pady=10, padx=10, fill="x")

    tk.Label(info_frame, text=f"Title: {title}", font=("Arial", 14, "bold"), bg="#D1C4E9").pack(anchor="w")
    tk.Label(info_frame, text=f"Date: {date} {time}", font=("Arial", 12), bg="#D1C4E9").pack(anchor="w")

    table_frame = tk.Frame(details_window, bg="#D1C4E9")
    table_frame.pack(pady=10, padx=10, fill="both", expand=True)

    table = ttk.Treeview(table_frame, columns=("Date","Category", "Amount", "Description"), show="headings")
    table.heading("Date", text="Date")
    table.heading("Category", text="Category")
    table.heading("Amount", text="Amount")
    table.heading("Description", text="Description")

    for name, value in category_totals.items():
        table.insert("", "end", values=(date, name, value, description))

    table.pack(pady=5, fill="both", expand=True)

    summary_frame = tk.Frame(details_window, bg="#D1C4E9")
    summary_frame.pack(fill="x", padx=10, pady=5)

    tk.Label(summary_frame, text=f"Budget left: {remaining}", font=("Arial", 12), bg="#D1C4E9").pack(side="left", padx=10)
    tk.Label(summary_frame, text=f"Total: {budget}", font=("Arial", 12), bg="#D1C4E9").pack(side="right", padx=10)

    fig, ax = plt.subplots()
    ax.pie(category_totals.values(), labels=category_totals.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    canvas = FigureCanvasTkAgg(fig, master=details_window)
    canvas.get_tk_widget().pack(pady=10)
    canvas.draw()

# Search functionality
def search_data():
    query = search_var.get()
    load_data(query)

# Delete selected entry
def delete_selected():
    selected_item = tree.selection()
    if not selected_item:
        return

    item = tree.item(selected_item)
    title, date, time = item['values'][0], item['values'][1], item['values'][2]

    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM summaries WHERE title = ? AND date = ? AND time = ?", (title, date, time))
    conn.commit()
    conn.close()

    load_data()

# GUI Setup
root = tk.Tk()
root.title("Budget Summary History")
root.geometry("1000x550")
root.configure(bg="#6200EA")

search_var = tk.StringVar()
ttk.Entry(root, textvariable=search_var).pack(pady=5, padx=10, fill="x")
ttk.Button(root, text="Search", command=search_data).pack()

tree = ttk.Treeview(root, columns=("Title", "Date", "Time", "Budget", "Total Spent", "Remaining", "Description"), show="headings")
for col in ("Title", "Date", "Time", "Budget", "Total Spent", "Remaining", "Description"):
    tree.heading(col, text=col)
tree.pack(pady=10, fill="both", expand=True)
tree.bind("<Double-1>", show_pie_chart_for_selection)

ttk.Button(root, text="Delete Selected", command=delete_selected).pack(pady=10)

init_db()
insert_sample_data()
load_data()
root.mainloop()
