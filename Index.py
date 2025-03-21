import tkinter as tk
from tkinter import ttk
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Database setup
def init_db():
    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        date TEXT,
                        total_spent REAL,
                        remaining REAL,
                        categories TEXT)''')
    conn.commit()
    conn.close()

def insert_sample_data():
    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM summaries")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ("March Budget Summary", "March 31, 2025", 1500.00, 200.00, "Food:500,Transportation:300,Utilities:400,Rent:200,Entertainment:100"),
            ("February Budget Summary", "February 28, 2025", 1200.00, 300.00, "Transportation:500,Food:700"),
            ("January Budget Summary", "January 31, 2025", 1800.00, 150.00, "Utilities:1000,Food:800"),
            ("December Budget Summary", "December 31, 2024", 2500.00, 500.00, "Rent:2000,Food:500"),
            ("November Budget Summary", "November 30, 2024", 1600.00, 400.00, "Entertainment:1000,Food:600"),
            ("October Budget Summary", "October 31, 2024", 900.00, 200.00, "Other:900")
        ]
        cursor.executemany("INSERT INTO summaries (title, date, total_spent, remaining, categories) VALUES (?, ?, ?, ?, ?)", sample_data)
    conn.commit()
    conn.close()

def load_data(search_query=""):
    for row in tree.get_children():
        tree.delete(row)
    
    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    if search_query:
        cursor.execute("SELECT title, date, total_spent, remaining FROM summaries WHERE title LIKE ?", (f"%{search_query}%",))
    else:
        cursor.execute("SELECT title, date, total_spent, remaining FROM summaries")
    rows = cursor.fetchall()
    conn.close()
    
    for row in rows:
        tree.insert("", "end", values=row)

def show_pie_chart_for_selection(event):
    selected_item = tree.selection()
    if not selected_item:
        return
    
    item = tree.item(selected_item)
    title = item['values'][0]
    
    conn = sqlite3.connect("budget_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT categories FROM summaries WHERE title = ?", (title,))
    data = cursor.fetchone()
    conn.close()
    
    if not data:
        return
    
    category_totals = {}
    categories = data[0].split(',')
    details_text = ""
    for category in categories:
        name, value = category.split(':')
        value = float(value)
        category_totals[name] = category_totals.get(name, 0) + value
        details_text += f"{name}: {value}\n"
    
    labels = list(category_totals.keys())
    values = list(category_totals.values())
    
    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    
    details_window = tk.Toplevel(root)
    details_window.title(f"Budget Details - {title}")
    details_window.configure(bg="#6200EA")
    
    details_label = tk.Label(details_window, text=details_text, justify="left", font=("Arial", 12), bg="#D1C4E9", fg="black", padx=10, pady=10)
    details_label.pack(pady=5, fill="both", expand=True)
    
    canvas = FigureCanvasTkAgg(fig, master=details_window)
    canvas.get_tk_widget().pack()
    canvas.draw()

def search_data():
    query = search_var.get()
    load_data(query)

# GUI Setup
root = tk.Tk()
root.title("Budget Summary History")
root.geometry("900x500")
root.configure(bg="#6200EA")

header_frame = tk.Frame(root, bg="#6200EA")
header_frame.pack(fill="x")
header_label = tk.Label(header_frame, text="SAVED ITEMS", font=("Arial", 14, "bold"), bg="#D1C4E9", padx=10, pady=5)
header_label.pack(side="left", padx=10, pady=5)

search_var = tk.StringVar()
search_entry = ttk.Entry(root, textvariable=search_var)
search_entry.pack(pady=5, padx=10, fill="x")

search_button = ttk.Button(root, text="Search", command=search_data)
search_button.pack()

tree = ttk.Treeview(root, columns=("Title", "Date", "Total Spent", "Remaining"), show="headings")
tree.heading("Title", text="Title")
tree.heading("Date", text="Date Completed")
tree.heading("Total Spent", text="Total Spent")
tree.heading("Remaining", text="Remaining Budget")
tree.pack(pady=10, fill="both", expand=True)

tree.bind("<Double-1>", show_pie_chart_for_selection)

# Initialize Database
init_db()
insert_sample_data()
load_data()

root.mainloop()
