import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import calendar
import pandas as pd
import json
from tkcalendar import DateEntry
import os

class ExpenseTracker:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Expense Tracker")
        self.root.geometry("1200x800")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Load settings and budgets
        self.load_settings()
        
        # Initialize database
        self.setup_database()
        
        # Create main frames
        self.create_frames()
        
        # Create all widgets
        self.create_input_widgets()
        self.create_filter_widgets()
        self.create_display_widgets()
        self.create_analysis_widgets()
        self.create_budget_widgets()
        
        # Load initial data
        self.load_expenses()
        self.update_summary()
        self.check_budget_alerts()
        
        # Bind closing event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def load_settings(self):
        self.settings_file = 'expense_settings.json'
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = {
                'budgets': {
                    'Food': 500,
                    'Transport': 200,
                    'Bills': 1000,
                    'Entertainment': 300,
                    'Shopping': 400,
                    'Health': 200,
                    'Other': 300
                },
                'categories': [
                    'Food', 'Transport', 'Bills', 'Entertainment',
                    'Shopping', 'Health', 'Other'
                ]
            }
            self.save_settings()
            
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
            
    def setup_database(self):
        self.conn = sqlite3.connect('expenses.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY,
                date TEXT,
                category TEXT,
                amount REAL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
    def create_frames(self):
        # Top frame for filters
        self.filter_frame = ctk.CTkFrame(self.root)
        self.filter_frame.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Left frame for input and budget
        self.left_frame = ctk.CTkFrame(self.root)
        self.left_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        # Middle frame for list
        self.list_frame = ctk.CTkFrame(self.root)
        self.list_frame.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        
        # Right frame for analysis
        self.analysis_frame = ctk.CTkFrame(self.root)
        self.analysis_frame.grid(row=1, column=2, padx=10, pady=5, sticky="nsew")
        
        # Configure grid weights
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
    def create_filter_widgets(self):
        # Date range filters
        ctk.CTkLabel(self.filter_frame, text="Date Range:").pack(side="left", padx=5)
        self.start_date = DateEntry(self.filter_frame, width=12, background='darkblue', 
                                  foreground='white', borderwidth=2)
        self.start_date.pack(side="left", padx=5)
        
        self.end_date = DateEntry(self.filter_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.pack(side="left", padx=5)
        
        # Search entry
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(self.filter_frame, placeholder_text="Search...",
                                       textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=5)
        
        # Category filter
        self.filter_category_var = ctk.StringVar(value="All Categories")
        self.filter_category = ctk.CTkOptionMenu(self.filter_frame, 
                                               values=["All Categories"] + self.settings['categories'],
                                               variable=self.filter_category_var)
        self.filter_category.pack(side="left", padx=5)
        
        # Apply filters button
        self.apply_filter_btn = ctk.CTkButton(self.filter_frame, text="Apply Filters",
                                            command=self.apply_filters)
        self.apply_filter_btn.pack(side="left", padx=5)
        
        # Export button
        self.export_btn = ctk.CTkButton(self.filter_frame, text="Export to CSV",
                                      command=self.export_to_csv)
        self.export_btn.pack(side="right", padx=5)
        
    def create_budget_widgets(self):
        # Budget frame
        self.budget_frame = ctk.CTkFrame(self.left_frame)
        self.budget_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(self.budget_frame, text="Budget Settings",
                    font=("Arial", 14, "bold")).pack(pady=5)
        
        # Budget entries for each category
        self.budget_entries = {}
        for category in self.settings['categories']:
            frame = ctk.CTkFrame(self.budget_frame)
            frame.pack(fill="x", padx=5, pady=2)
            
            ctk.CTkLabel(frame, text=category).pack(side="left")
            entry = ctk.CTkEntry(frame, width=100)
            entry.insert(0, str(self.settings['budgets'][category]))
            entry.pack(side="right", padx=5)
            self.budget_entries[category] = entry
            
        # Save budget button
        ctk.CTkButton(self.budget_frame, text="Save Budgets",
                     command=self.save_budgets).pack(pady=5)
        
    def create_analysis_widgets(self):
        # Notebook for different charts
        self.notebook = ctk.CTkTabview(self.analysis_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add tabs
        self.notebook.add("Summary")
        self.notebook.add("Trends")
        self.notebook.add("Categories")
        
        # Summary tab
        self.summary_text = ctk.CTkTextbox(self.notebook.tab("Summary"))
        self.summary_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Trends tab - Line chart
        self.fig_trends, self.ax_trends = plt.subplots(figsize=(6, 4))
        self.canvas_trends = FigureCanvasTkAgg(self.fig_trends,
                                              master=self.notebook.tab("Trends"))
        self.canvas_trends.get_tk_widget().pack(fill="both", expand=True)
        
        # Categories tab - Pie chart
        self.fig_pie, self.ax_pie = plt.subplots(figsize=(6, 4))
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie,
                                           master=self.notebook.tab("Categories"))
        self.canvas_pie.get_tk_widget().pack(fill="both", expand=True)
    def create_input_widgets(self):
        # Input section title
        ctk.CTkLabel(self.input_frame, text="Add New Expense", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Date picker
        self.date_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Date (YYYY-MM-DD)")
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.pack(padx=10, pady=5, fill="x")
        
        # Category dropdown
        self.categories = ["Food", "Transport", "Bills", "Entertainment", "Shopping", "Health", "Other"]
        self.category_var = ctk.StringVar(value=self.categories[0])
        self.category_dropdown = ctk.CTkOptionMenu(self.input_frame, values=self.categories, variable=self.category_var)
        self.category_dropdown.pack(padx=10, pady=5, fill="x")
        
        # Amount entry
        self.amount_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Amount")
        self.amount_entry.pack(padx=10, pady=5, fill="x")
        
        # Description entry
        self.description_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Description")
        self.description_entry.pack(padx=10, pady=5, fill="x")
        
        # Add button
        self.add_button = ctk.CTkButton(self.input_frame, text="Add Expense", command=self.add_expense)
        self.add_button.pack(padx=10, pady=10, fill="x")
        
       
    def apply_filters(self):
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        search_term = self.search_var.get()
        category = self.filter_category_var.get()
        
        query = '''
            SELECT date, category, amount, description
            FROM expenses
            WHERE date BETWEEN ? AND ?
        '''
        params = [start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')]
        
        if category != "All Categories":
            query += ' AND category = ?'
            params.append(category)
            
        if search_term:
            query += ' AND (description LIKE ? OR category LIKE ?)'
            params.extend(['%' + search_term + '%'] * 2)
            
        query += ' ORDER BY date DESC'
        
        self.cursor.execute(query, params)
        self.display_filtered_results(self.cursor.fetchall())
        
    def display_filtered_results(self, results):
        self.expenses_text.delete('1.0', 'end')
        for expense in results:
            self.expenses_text.insert('end',
                f"Date: {expense[0]}\n"
                f"Category: {expense[1]}\n"
                f"Amount: ${expense[2]:.2f}\n"
                f"Description: {expense[3]}\n"
                f"{'-'*40}\n"
            )
        self.update_summary()
        
    def export_to_csv(self):
        df = pd.read_sql_query('''
            SELECT date, category, amount, description
            FROM expenses
            ORDER BY date DESC
        ''', self.conn)
        
        filename = f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        self.show_message("Export Successful", f"Data exported to {filename}")
        
    def save_budgets(self):
        for category, entry in self.budget_entries.items():
            try:
                self.settings['budgets'][category] = float(entry.get())
            except ValueError:
                self.show_error(f"Invalid budget value for {category}")
                return
        
        self.save_settings()
        self.show_message("Success", "Budgets saved successfully!")
        self.check_budget_alerts()
        
    def check_budget_alerts(self):
        # Get current month's expenses
        current_month = datetime.now().strftime('%Y-%m')
        self.cursor.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            WHERE date LIKE ?
            GROUP BY category
        ''', (current_month + '%',))
        
        expenses = dict(self.cursor.fetchall())
        
        # Check each category
        alerts = []
        for category, budget in self.settings['budgets'].items():
            if category in expenses and expenses[category] > budget:
                alerts.append(f"{category}: ${expenses[category]:.2f} / ${budget:.2f}")
                
        if alerts:
            self.show_alert("Budget Alerts",
                          "The following categories are over budget:\n\n" +
                          "\n".join(alerts))
            
    def update_summary(self):
        # Calculate total expenses
        self.cursor.execute('SELECT SUM(amount) FROM expenses')
        total = self.cursor.fetchone()[0] or 0
        
        # Calculate expenses by category
        self.cursor.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            GROUP BY category
        ''')
        category_totals = self.cursor.fetchall()
        
        # Update summary text
        self.summary_text.delete('1.0', 'end')
        self.summary_text.insert('end', f"Total Expenses: ${total:.2f}\n\n")
        for category, amount in category_totals:
            budget = self.settings['budgets'].get(category, 0)
            self.summary_text.insert('end',
                f"{category}:\n"
                f"  Spent: ${amount:.2f}\n"
                f"  Budget: ${budget:.2f}\n"
                f"  {'Over budget by' if amount > budget else 'Under budget by'}: "
                f"${abs(amount - budget):.2f}\n\n"
            )
            
        # Update pie chart
        self.ax_pie.clear()
        if category_totals:
            categories, amounts = zip(*category_totals)
            self.ax_pie.pie(amounts, labels=categories, autopct='%1.1f%%')
            self.ax_pie.set_title("Expenses by Category")
        self.canvas_pie.draw()
        
        # Update trends chart
        self.update_trends_chart()
        
    def update_trends_chart(self):
        # Get daily totals for the last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.cursor.execute('''
            SELECT date, SUM(amount)
            FROM expenses
            WHERE date >= ?
            GROUP BY date
            ORDER BY date
        ''', (thirty_days_ago,))
        
        dates, amounts = zip(*self.cursor.fetchall()) if self.cursor.fetchall() else ([], [])
        
        self.ax_trends.clear()
        if dates:
            self.ax_trends.plot(dates, amounts)
            self.ax_trends.set_title("Daily Expenses (Last 30 Days)")
            self.ax_trends.set_xlabel("Date")
            self.ax_trends.set_ylabel("Amount ($)")
            plt.xticks(rotation=45)
            plt.tight_layout()
        self.canvas_trends.draw()
        
    def show_message(self, title, message):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("300x150")
        
        ctk.CTkLabel(dialog, text=message).pack(pady=20)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack()
        
    def show_alert(self, title, message):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x300")
        
        ctk.CTkLabel(dialog, text=message, text_color="red").pack(pady=20)
        ctk.CTkButton(dialog, text="OK", command=dialog.destroy).pack()
        
    def on_closing(self):
        self.save_settings()
        self.conn.close()
        self.root.destroy()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ExpenseTracker()
    app.run()