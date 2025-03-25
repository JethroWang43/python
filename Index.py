
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import sqlite3
import os


# Global variables
user_budget = 0  # Stores the user's budget
remaining_budget = 0  # Stores the remaining budget
day_count = 1  # Initialize the day counter
all_data = []  # List to store past days' data
total_amount = 0  # Initialize total amount
duration_days = 0  # Initialize duration days
DATABASE_NAME = "input.db"  # Database file name (updated to input.db)


def initialize_database():
    """Ensures the database and table exist, and inserts a default record if empty."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Create table if it does not exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            item TEXT NOT NULL,
            amount REAL NOT NULL,
            total_spent REAL NOT NULL
        )
    ''')

    # Check if the table is empty
    cursor.execute("SELECT COUNT(*) FROM expenses")
    count = cursor.fetchone()[0]

    # Insert a default record if the table is empty
    if count == 0:
        cursor.execute('''
            INSERT INTO expenses (date, category, item, amount, total_spent)
            VALUES ('List of Date','.','.','.','.')
        ''')
        print("Inserted default expense record.")

    conn.commit()
    conn.close()

    print("Database initialized successfully.")

initialize_database()


# Function to fetch all data from the database
def fetch_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date, category, item, amount FROM expenses")
    data = cursor.fetchall()
    conn.close()
    return data


# Function to switch to the second screen
def go_to_budget_screen():
    welcome_screen.pack_forget()  # Hide welcome screen
    budget_screen.pack()  # Show budget input screen


# Function to handle the submit button in the budget input screen
def submit_budget():
    global duration_days, user_budget, remaining_budget
    try:
        duration_days = int(duration_entry.get())
        user_budget = float(budget_entry.get())  # Store budget
        remaining_budget = user_budget  # Initialize remaining budget
       
        if duration_days <= 0 or user_budget <= 0:
            raise ValueError("Duration and Budget must be positive numbers.")
       
        budget_screen.pack_forget()  # Hide budget input screen
        create_expense_tracker_gui()  # Show expense tracker GUI
    except ValueError as e:
        messagebox.showerror("Invalid Input", str(e))


# Function to clear placeholder text on focus
def clear_placeholder(event):
    widget = event.widget
    if widget.get() == "Title" or widget.get() == "Enter Duration" or widget.get() == "Enter Budget":
        widget.delete(0, tk.END)
        widget.config(fg="black")


# Function to restore placeholder text if input is empty
def restore_placeholder(event):
    widget = event.widget
    if widget.get() == "":
        if widget == title_entry:
            widget.insert(0, "Title")
        elif widget == duration_entry:
            widget.insert(0, "Enter Duration")
        elif widget == budget_entry:
            widget.insert(0, "Enter Budget")
        widget.config(fg="grey")



# Function to show data
def show_data():
    global tree, search_entry

    # Create a new window
    data_window = tk.Toplevel()
    data_window.title("Budget Tracker")
    data_window.geometry("600x500")
    data_window.configure(bg="#6A0DAD")  # Purple background

    # Styling
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"), background="purple", foreground="black")

    # Frame to hold Treeview
    frame2 = tk.Frame(data_window, bg="#6A0DAD")
    frame2.pack(pady=20, padx=20, fill="both", expand=True)

    # Search Bar
    search_label = tk.Label(data_window, text="Search Date:", font=("Arial", 12, "bold"), bg="#6A0DAD", fg="white")
    search_label.pack(pady=5)
    search_entry = tk.Entry(data_window, font=("Arial", 12))
    search_entry.pack(pady=5, padx=10, fill="x")
   
    search_button = tk.Button(data_window, text="Search", command=lambda: fetch_data(search_entry.get()))
    search_button.pack(pady=5)

    # Create Treeview (Only showing Dates initially)
    tree = ttk.Treeview(frame2, columns=("Date",), show="headings")
    tree.heading("Date", text="Date")
    tree.pack(fill="both", expand=True)

    # Fetch unique dates from the database
    def fetch_data(search_term=""):
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()

        # Query with optional search filter
        if search_term:
            cursor.execute("SELECT DISTINCT date FROM expenses WHERE date LIKE ? ORDER BY date DESC", (f"%{search_term}%",))
        else:
            cursor.execute("SELECT DISTINCT date FROM expenses ORDER BY date DESC")
       
        records = cursor.fetchall()
        conn.close()

        # Clear existing rows
        for row in tree.get_children():
            tree.delete(row)

        # Insert dates into the Treeview
        for record in records:
            tree.insert("", "end", values=(record[0],))

        print("Dates Updated.")

    fetch_data()

    # Function to show details for a selected date
    def show_expenses_for_date(event):
        selected_item = tree.focus()
        if not selected_item:
            return

        values = tree.item(selected_item, "values")
        if not values:
            return

        selected_date = values[0]
        details_window = tk.Toplevel(data_window)
        details_window.title(f"Expenses on {selected_date}")
        details_window.geometry("1000x800")
        details_window.configure(bg="white")

        # Treeview to show details
        detail_tree = ttk.Treeview(details_window, columns=("Category", "Item", "Amount", "Total Spent"), show="headings")
        detail_tree.heading("Category", text="Category")
        detail_tree.heading("Item", text="Item")
        detail_tree.heading("Amount", text="Amount")
        detail_tree.heading("Total Spent", text="Total Spent")
        detail_tree.pack(fill="both", expand=True)

        # Fetch expenses for the selected date
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, item, amount, total_spent FROM expenses WHERE date = ?", (selected_date,))
        records = cursor.fetchall()
        conn.close()

        # Insert expense records into the detail treeview
        for record in records:
            detail_tree.insert("", "end", values=record)

        show_pie_chart(details_window, selected_date)




    # Function to delete all records for a selected date
    def delete_selected_date():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a date to delete.")
            return

        values = tree.item(selected_item, "values")
        if not values:
            return

        selected_date = values[0]

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete all expenses for {selected_date}?")
        if confirm:
            conn = sqlite3.connect("input.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE date = ?", (selected_date,))
            conn.commit()
            conn.close()

            # Remove from the treeview
            tree.delete(selected_item)

            print(f"Deleted all expenses for {selected_date}.")
            messagebox.showinfo("Deleted", f"All expenses for {selected_date} have been deleted.")

    # Function to display pie chart inside details window
    def show_pie_chart(window, selected_date):
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE date = ? GROUP BY category", (selected_date,))
        data = cursor.fetchall()
        conn.close()

        if not data:
            return  # No data to show

        labels = [str(row[0]) for row in data]
        sizes = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
        ax.set_title(f"Expense Distribution on {selected_date}")

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

    # Bind Treeview click event to open details window
    tree.bind("<ButtonRelease-1>", show_expenses_for_date)

    # Delete button
    delete_button = tk.Button(data_window, text="Delete Selected Date", command=delete_selected_date, bg="red", fg="white")
    delete_button.pack(pady=5)

    data_window.mainloop()

# Create the main window
root = tk.Tk()
root.title("Budget Buddy")
root.geometry("400x500")
root.configure(bg="purple")

# Expense Tracker GUI
def create_expense_tracker_gui():
    global date_entry, category_combo, item_entry, amount_entry, tree, day_label, total_label, remaining_label, root, remaining_budget


    root.geometry("880x450")


    # Initialize remaining budget
    remaining_budget = float(budget_entry.get())  # Convert user input to float


    # Style Configuration
    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Arial", 12, "bold"))


    # Day Label
    day_label = tk.Label(root, text=f"Day {day_count}", font=("Arial", 16, "bold"), fg="white", bg="purple")
    day_label.place(x=100, y=15)


    # Input Form
    form_frame = tk.Frame(root, bg="purple")
    form_frame.place(x=10, y=50)


    tk.Label(form_frame, text="Date", font=("Arial", 12, "bold"), fg="white", bg="purple").grid(row=0, column=0, sticky="w")
    date_entry = DateEntry(form_frame, font=("Arial", 12), width=18, background='darkblue', foreground='white', borderwidth=2)
    date_entry.grid(row=1, column=0, pady=5)


    tk.Label(form_frame, text="Category", font=("Arial", 12, "bold"), fg="white", bg="purple").grid(row=2, column=0, sticky="w")
    category_combo = ttk.Combobox(form_frame, font=("Arial", 12), width=18, values=["Food", "Transport", "Entertainment", "Rent", "Utilities", "Others"])
    category_combo.grid(row=3, column=0, pady=5)


    tk.Label(form_frame, text="Item", font=("Arial", 12, "bold"), fg="white", bg="purple").grid(row=4, column=0, sticky="w")
    item_entry = tk.Entry(form_frame, font=("Arial", 12), width=20, bg="lightyellow")
    item_entry.grid(row=5, column=0, pady=5)


    tk.Label(form_frame, text="Amount", font=("Arial", 12, "bold"), fg="white", bg="purple").grid(row=6, column=0, sticky="w")
    amount_entry = tk.Entry(form_frame, font=("Arial", 12), width=20, bg="lightyellow")
    amount_entry.grid(row=7, column=0, pady=5)


    # Button Frame (Insert & Next Side by Side)
    button_frame = tk.Frame(form_frame, bg="purple")
    button_frame.grid(row=8, column=0, pady=10, columnspan=2)


    tk.Button(button_frame, text="Insert", font=("Arial", 12, "bold"), bg="lightyellow", command=insert_data).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Next", font=("Arial", 12, "bold"), bg="lightyellow", command=next_day).pack(side=tk.LEFT, padx=5)


    # Table Frame
    table_frame = tk.Frame(root, bg="lightgray", bd=2)
    table_frame.place(x=250, y=50, width=600, height=300)


    # Table Header and Treeview
    columns = ("Date", "Category", "Item", "Amount")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")


    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")


    tree.pack(expand=True, fill="both")


    # Remaining & Total Section
    footer_frame = tk.Frame(root, bg="lightyellow", padx=10, pady=5)
    footer_frame.place(x=250, y=360, width=600)


    tk.Label(footer_frame, text="Remaining:", font=("Arial", 12, "bold"), bg="lightyellow").grid(row=0, column=0, sticky="w")


    # Remaining Budget Label
    remaining_label = tk.Label(footer_frame, text=f"{remaining_budget:.2f}", font=("Arial", 12, "bold"), bg="lightyellow")
    remaining_label.grid(row=0, column=1, sticky="w")


    # Total Amount Label
    total_label = tk.Label(footer_frame, text="Total: 0.00", font=("Arial", 12, "bold"), bg="lightyellow")
    total_label.grid(row=0, column=2, sticky="e")


# Functions for expense tracker
def save_to_database(date, category, item, amount, total_spent):
    """Saves the given expense data to the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (date, category, item, amount, total_spent)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, category, item, amount, total_spent))
    conn.commit()
    conn.close()


def insert_data():
    """Inserts data into the table and updates the total amount and remaining budget."""
    global total_amount, remaining_budget


    date = date_entry.get()
    category = category_combo.get()
    item = item_entry.get()
    amount = amount_entry.get()

    if date and category and item and amount:
        try:
            amount = float(amount)  # Convert amount to float
            if amount > remaining_budget:
                messagebox.showwarning("Warning", "You don't have enough budget for this expense!")
                return


            tree.insert("", "end", values=(date, category, item, f"{amount:.2f}"))
            total_amount += amount  # Update total amount
            remaining_budget -= amount  # Deduct from remaining budget


            update_total_label()  # Update budget balance
            save_to_database(date, category, item, amount, total_amount)  # Save to database
            reset_inputs()

        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a number.")
    else:
        messagebox.showerror("Missing Data", "Please complete all fields before inserting.")
       
       
def reset_inputs():
    """Clears input fields but does NOT change the date (handled in next_day)."""
    category_combo.set("")  # Reset category selection
    item_entry.delete(0, tk.END)  # Clear item field
    amount_entry.delete(0, tk.END)  # Clear amount field




from datetime import timedelta

def next_day():
    """Progresses the day count, updates the date, and resets inputs."""
    global day_count, all_data, total_amount
    
    # Check if there is at least one entry before proceeding
    if not tree.get_children():
        messagebox.showwarning("No Data Entered", "Please insert at least one expense before moving to the next day.")
        return

    # Save the current day's data
    day_data = []
    for item in tree.get_children():
        day_data.append(tree.item(item)["values"])  # Store row data

    if day_data:
        all_data.append((f"Day {day_count}", day_data))  # Store with day label

    if day_count == duration_days:  # Display table and pie chart when duration is reached
        all_expenses = [item for day, data in all_data for item in data]
        budget = [remaining_budget]  # For calculations
        display_table_Chart(all_expenses, budget)  # Display table and chart
        return

    # ✅ Increment the day count
    day_count += 1
    day_label.config(text=f"Day {day_count}")

    # ✅ Increment the date by 1 day
    current_date = date_entry.get_date()
    new_date = current_date + timedelta(days=1)
    date_entry.set_date(new_date)  # Update the date field

    # Clear the table for the new day
    tree.delete(*tree.get_children())

    # Reset input fields (keeps new date)
    reset_inputs()

def reset_program():
    """Reset all global variables and rebuild the welcome screen"""
    global day_count, all_data, total_amount, remaining_budget, user_budget, duration_days
    
    # Reset all global variables
    day_count = 0
    all_data = []
    total_amount = 0
    remaining_budget = 0
    user_budget = 0
    duration_days = 0
    
    # Clear all widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Rebuild the welcome screen
    root.geometry("400x500")
    root.configure(bg="purple")
    
    # Welcome Screen
    welcome_screen = tk.Frame(root, bg="purple")
    welcome_screen.pack(fill="both", expand=True)
    
    welcome_label = tk.Label(welcome_screen, text="WELCOME", font=("Arial", 18, "bold"), fg="white", bg="purple")
    welcome_label.pack(pady=20)
    
    app_name_label = tk.Label(welcome_screen, text="Budget Buddy", font=("Arial", 16, "bold"), fg="white", bg="purple")
    app_name_label.pack(pady=10)
    
    start_button = tk.Button(welcome_screen, text="START YOUR JOURNEY!", font=("Arial", 12, "bold"),
                           bg="lightgray", command=go_to_budget_screen)
    start_button.pack(pady=20)
    
    save_button = tk.Button(welcome_screen, text="Show List", command=show_data, font=("Arial", 16, "bold"), fg="white", bg="purple")
    save_button.pack(pady=30)

def update_total_label():
    """Updates the total and remaining budget labels."""
    total_label.config(text=f"Total: {total_amount:.2f}")  # Format to 2 decimal places
    remaining_label.config(text=f" {remaining_budget:.2f}")  # Remove extra "Remaining:"
   


def display_table_Chart(data, budget):  
    global chart_frame


    root.geometry("")


    for widget in root.winfo_children():
        widget.destroy()


    header = tk.Label(root, text="Duration Complete", font=("Arial", 14, "bold"))
    header.pack(side="top", fill="x")


    content_frame = tk.Frame(root)
    content_frame.pack(side="top", fill="both", expand=True, padx=20, pady=10)


    table_frame = tk.Frame(content_frame)
    table_frame.pack(side="top", fill="both", expand=True, pady=(0, 10))


    height_database = min(len(data), 50)
    table = ttk.Treeview(table_frame, columns=("Date", "Category", "Item", "Amount"), show="headings", height=height_database)


    table.heading("Date", text="Date", anchor="center")
    table.heading("Category", text="Category", anchor="center")
    table.heading("Item", text="Item", anchor="center")
    table.heading("Amount", text="Amount", anchor="center")


    table.column("Date", width=120, anchor="center")
    table.column("Category", width=120, anchor="center")
    table.column("Item", width=120, anchor="center")
    table.column("Amount", width=120, anchor="center")


    total_expenses = 0  # Initialize total expenses


    for row in data:
        table.insert("", "end", values=row)
        total_expenses += float(row[3])


    table.pack(side="top", fill="both", expand=True, padx=10, pady=5)
    table.tag_configure("summary", font=("Arial", 10, "bold"))


    budget_left = budget[0]


    budget_row = ("Budget Left", f"{budget_left:.2f}", "TOTAL", f"{total_expenses:.2f}")


    table.insert("", "end", values=budget_row, tags=("summary",))


    if 'chart_frame' in globals() and chart_frame.winfo_exists():
        chart_frame.destroy()


    chart_frame = tk.Frame(content_frame)
    chart_frame.pack(side="top", fill="both", expand=True, pady=(10, 20))


    for_pie_chart(data)


    button_frame = tk.Frame(content_frame)
    button_frame.pack(side="top", fill="x", pady=(10, 20))


    save_button = tk.Button(button_frame, text="SAVE", command=show_data)
    save_button.pack(side="top", padx=20, pady=5)

    back_button = tk.Button(button_frame, text="Back to Main", 
                        command=reset_to_main,  # Calls the fixed reset function
                        bg="blue", fg="white")  
    back_button.pack(side="top", padx=20, pady=5) 
    
    messagebox.showinfo("Information", f"Congrats you have completed the duration. You have saved {budget_left:.2f}")
    messagebox.showwarning("Attention", "Press save if you want to visit your history.")


def for_pie_chart(data):
    global chart_frame

    category_totals = {}

    for row in data:
        category = row[1]
        amount = float(row[3])


        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount


    labels = list(category_totals.keys())
    values = list(category_totals.values())


    fig = Figure(figsize=(4, 4), dpi=100)
    plot = fig.add_subplot(111)


    if sum(values) > 0:
        plot.pie(values, labels=labels, autopct="%1.1f%%")
        plot.set_title("Price of Categories based on Budget")
    else:
        plot.text(0.5, 0.5, "No data available", ha='center', va='center')

    canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill=tk.BOTH, expand=True)
    canvas.draw()


def delete_data():
    """Deletes all data from the database."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses")
    conn.commit()
    conn.close()
    messagebox.showinfo("Success", "All data has been deleted.")




# Function to show data
def show_data():
    global tree, search_entry

    # Create a new window
    data_window = tk.Toplevel()
    data_window.title("Budget Tracker")
    data_window.geometry("600x500")
    data_window.configure(bg="#6A0DAD")  # Purple background

    # Styling
    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 12), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 14, "bold"), background="purple", foreground="black")

    # Frame to hold Treeview
    frame2 = tk.Frame(data_window, bg="#6A0DAD")
    frame2.pack(pady=20, padx=20, fill="both", expand=True)

    # Search Bar
    search_label = tk.Label(data_window, text="Search Date:", font=("Arial", 12, "bold"), bg="#6A0DAD", fg="white")
    search_label.pack(pady=5)
    search_entry = tk.Entry(data_window, font=("Arial", 12))
    search_entry.pack(pady=5, padx=10, fill="x")
   
    search_button = tk.Button(data_window, text="Search", command=lambda: fetch_data(search_entry.get()))
    search_button.pack(pady=5)

    # Create Treeview (Only showing Dates initially)
    tree = ttk.Treeview(frame2, columns=("Date",), show="headings")
    tree.heading("Date", text="Date")
    tree.pack(fill="both", expand=True)

    # Fetch unique dates from the database
    def fetch_data(search_term=""):
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()

        # Query with optional search filter
        if search_term:
            cursor.execute("SELECT DISTINCT date FROM expenses WHERE date LIKE ? ORDER BY date DESC", (f"%{search_term}%",))
        else:
            cursor.execute("SELECT DISTINCT date FROM expenses ORDER BY date DESC")
       
        records = cursor.fetchall()
        conn.close()

        # Clear existing rows
        for row in tree.get_children():
            tree.delete(row)

        # Insert dates into the Treeview
        for record in records:
            tree.insert("", "end", values=(record[0],))

        print("Dates Updated.")

    fetch_data()

    # Function to show details for a selected date
    def show_expenses_for_date(event):
        selected_item = tree.focus()
        if not selected_item:
            return

        values = tree.item(selected_item, "values")
        if not values:
            return

        selected_date = values[0]
        details_window = tk.Toplevel(data_window)
        details_window.title(f"Expenses on {selected_date}")
        details_window.geometry("1000x800")
        details_window.configure(bg="white")

        # Treeview to show details
        detail_tree = ttk.Treeview(details_window, columns=("Category", "Item", "Amount", "Total Spent"), show="headings")
        detail_tree.heading("Category", text="Category")
        detail_tree.heading("Item", text="Item")
        detail_tree.heading("Amount", text="Amount")
        detail_tree.heading("Total Spent", text="Total Spent")
        detail_tree.pack(fill="both", expand=True)

        # Fetch expenses for the selected date
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, item, amount, total_spent FROM expenses WHERE date = ?", (selected_date,))
        records = cursor.fetchall()
        conn.close()

        # Insert expense records into the detail treeview
        for record in records:
            detail_tree.insert("", "end", values=record)

        show_pie_chart(details_window, selected_date)




    # Function to delete all records for a selected date
    def delete_selected_date():
        selected_item = tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a date to delete.")
            return

        values = tree.item(selected_item, "values")
        if not values:
            return

        selected_date = values[0]

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete all expenses for {selected_date}?")
        if confirm:
            conn = sqlite3.connect("input.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM expenses WHERE date = ?", (selected_date,))
            conn.commit()
            conn.close()

            # Remove from the treeview
            tree.delete(selected_item)

            print(f"Deleted all expenses for {selected_date}.")
            messagebox.showinfo("Deleted", f"All expenses for {selected_date} have been deleted.")

    # Function to display pie chart inside details window
    def show_pie_chart(window, selected_date):
        conn = sqlite3.connect("input.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, SUM(amount) FROM expenses WHERE date = ? GROUP BY category", (selected_date,))
        data = cursor.fetchall()
        conn.close()

        if not data:
            return  # No data to show

        labels = [str(row[0]) for row in data]
        sizes = [row[1] for row in data]

        fig, ax = plt.subplots(figsize=(4, 4))
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
        ax.set_title(f"Expense Distribution on {selected_date}")

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=10)

    # Bind Treeview click event to open details window
    tree.bind("<ButtonRelease-1>", show_expenses_for_date)

    # Delete button
    delete_button = tk.Button(data_window, text="Delete Selected Date", command=delete_selected_date, bg="red", fg="white")
    delete_button.pack(pady=5)

    data_window.mainloop()



from datetime import datetime

def reset_to_main():
    """Completely resets the program and returns to the main screen without a blank screen."""
    global day_count, total_amount, remaining_budget, user_budget, duration_days

    # ✅ Destroy all widgets first
    for widget in root.winfo_children():
        widget.destroy()

    # ✅ Rebuild the UI immediately before resetting variables
    main()

    # ✅ Now reset the variables after UI is loaded
    day_count = 1
    total_amount = 0
    remaining_budget = 0
    user_budget = 0
    duration_days = 0

    # ✅ Reset all input fields
    title_entry.delete(0, tk.END)
    title_entry.insert(0, "Title")

    duration_entry.delete(0, tk.END)
    duration_entry.insert(0, "Enter Duration")

    budget_entry.delete(0, tk.END)
    budget_entry.insert(0, "Enter Budget")

    # ✅ Reset DateEntry to today's date
    if date_entry:
        date_entry.set_date(datetime.today())

#Main program
def main():
    """Rebuilds the main screen after reset."""
    global welcome_screen, budget_screen, title_entry, duration_entry, budget_entry

    root.geometry("400x500")
    root.configure(bg="purple")

    # Welcome Screen
    welcome_screen = tk.Frame(root, bg="purple")
    welcome_screen.pack(fill="both", expand=True)

    welcome_label = tk.Label(welcome_screen, text="WELCOME", font=("Arial", 18, "bold"), fg="white", bg="purple")
    welcome_label.pack(pady=20)

    app_name_label = tk.Label(welcome_screen, text="Budget Buddy", font=("Arial", 16, "bold"), fg="white", bg="purple")
    app_name_label.pack(pady=10)

    # Start Journey Button
    start_button = tk.Button(welcome_screen, text="START YOUR JOURNEY!", font=("Arial", 12, "bold"),
                             bg="lightgray", command=go_to_budget_screen)
    start_button.pack(pady=20)

    # Show Data Button (Show List)
    save_button = tk.Button(welcome_screen, text="Show List", font=("Arial", 16, "bold"), fg="white", bg="purple",
                            command=show_data)
    save_button.pack(pady=30)

    # Budget Input Screen
    budget_screen = tk.Frame(root, bg="purple")

    title_label = tk.Label(budget_screen, text="Let's start your budgeting journey",
                           font=("Arial", 16, "bold"), fg="white", bg="purple")
    title_label.pack(pady=20)

    title_entry = tk.Entry(budget_screen, width=30, font=("Arial", 12), fg="grey")
    title_entry.insert(0, "Title")
    title_entry.bind("<FocusIn>", clear_placeholder)
    title_entry.bind("<FocusOut>", restore_placeholder)
    title_entry.pack(pady=5)

    duration_entry = tk.Entry(budget_screen, width=30, font=("Arial", 12), fg="grey")
    duration_entry.insert(0, "Enter Duration")
    duration_entry.bind("<FocusIn>", clear_placeholder)
    duration_entry.bind("<FocusOut>", restore_placeholder)
    duration_entry.pack(pady=5)

    budget_entry = tk.Entry(budget_screen, width=30, font=("Arial", 12), fg="grey")
    budget_entry.insert(0, "Enter Budget")
    budget_entry.bind("<FocusIn>", clear_placeholder)
    budget_entry.bind("<FocusOut>", restore_placeholder)
    budget_entry.pack(pady=5)
    

    submit_button = tk.Button(budget_screen, text="SUBMIT", font=("Arial", 12, "bold"), bg="lightgray",
                              command=submit_budget)
    submit_button.pack(pady=20)

main()  # Initialize the UI

root.mainloop()  # Run Tkinter main loop
