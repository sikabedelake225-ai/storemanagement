# Store_Management_Final.py
# Store Management System (Dark Mode) - with login + date filtering for Sales & Credits
import csv
import datetime
import os
import zipfile
import tkinter as tk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pandas as pd
import hashlib

# ---------------------------
# DYNAMIC STORAGE PATH
# ---------------------------
DATA_DIR = "data"

# Create folder dynamically if not exist
os.makedirs(DATA_DIR, exist_ok=True)

# File definitions (inside folder)
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.csv")
SALES_FILE = os.path.join(DATA_DIR, "sales.csv")
CREDIT_FILE = os.path.join(DATA_DIR, "credit_sales.csv")
USERS_FILE = os.path.join(DATA_DIR, "users.csv")


# ---------------------------
# UTIL & INITIALIZATION
# ---------------------------
def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def initialize_files():
    files = [
        (PRODUCTS_FILE, ["ID", "Name", "Price", "Quantity", "Registration_Date"]),
        (SALES_FILE, ["Sale_Number", "Product_ID", "Product_Name", "Quantity_Sold", "Total_Amount", "Money_Given", "Change_Returned", "Payment_Method", "Sale_Date"]),
        (CREDIT_FILE, ["Credit_ID", "Customer_Name", "Product_ID", "Product_Name", "Quantity_Sold", "Total_Amount", "Amount_Paid", "Balance", "Credit_Date"]),
        (USERS_FILE, ["Username", "PasswordHash", "Role"])
    ]
    for file, headers in files:
        if not os.path.exists(file):
            with open(file, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(headers)
    # create default admin if none exists
    users = read_csv(USERS_FILE)
    if not users:
        with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
            # default admin: admin / admin123
            csv.writer(f).writerow(["admin", sha256("admin123"), "admin"])

def read_csv(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except:
        return []

def write_csv(file, rows, fieldnames):
    with open(file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def generate_id(file, prefix, field):
    try:
        with open(file, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
            if reader:
                last_id = reader[-1][field]
                num = int(''.join(filter(str.isdigit, last_id))) + 1
                return f"{prefix}{num:03d}"
    except:
        pass
    return f"{prefix}001"

# ---------------------------
# PRODUCT MANAGEMENT
# ---------------------------
def add_product_gui(name, price, quantity, refresh_callback=None):
    if not name or not price or not quantity:
        messagebox.showerror("Error", "Please fill all fields.")
        return
    try:
        price = float(price)
        quantity = int(quantity)
    except:
        messagebox.showerror("Error", "Invalid price or quantity.")
        return

    pid = generate_id(PRODUCTS_FILE, "PROD", "ID")
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(PRODUCTS_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([pid, name, price, quantity, date])

    messagebox.showinfo("Success", f"✅ Product '{name}' added successfully!")
    if refresh_callback:
        refresh_callback()

def modify_product_gui(pid, new_name, new_price, new_qty, refresh_callback=None):
    if not pid:
        messagebox.showerror("Error", "Enter Product ID.")
        return

    confirm = messagebox.askyesno("Confirm Update", f"Are you sure you want to update Product '{pid}'?")
    if not confirm:
        return

    rows = read_csv(PRODUCTS_FILE)
    found = False
    for r in rows:
        if r["ID"] == pid:
            if new_name:
                r["Name"] = new_name
            if new_price:
                try:
                    r["Price"] = str(float(new_price))
                except:
                    messagebox.showerror("Error", "Invalid price.")
                    return
            if new_qty:
                try:
                    r["Quantity"] = str(int(new_qty))
                except:
                    messagebox.showerror("Error", "Invalid quantity.")
                    return
            found = True
            break

    if not found:
        messagebox.showerror("Error", "Product not found.")
        return

    write_csv(PRODUCTS_FILE, rows, rows[0].keys())
    messagebox.showinfo("Success", "✅ Product updated successfully!")
    if refresh_callback:
        refresh_callback()

def delete_product_gui(pid, refresh_callback=None):
    if not pid:
        messagebox.showerror("Error", "Please enter Product ID.")
        return

    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete Product '{pid}'?")
    if not confirm:
        return

    rows = read_csv(PRODUCTS_FILE)
    filtered = [r for r in rows if r["ID"] != pid]

    if len(filtered) == len(rows):
        messagebox.showerror("Error", f"Product ID '{pid}' not found.")
        return

    write_csv(PRODUCTS_FILE, filtered, rows[0].keys())
    messagebox.showinfo("Deleted", f"🗑 Product '{pid}' deleted successfully.")
    if refresh_callback:
        refresh_callback()

# ---------------------------
# SALES & CREDIT MANAGEMENT
# ---------------------------
def record_sale_gui(pid, qty, money, method, refresh_callback=None):
    try:
        qty = int(qty)
        money = float(money)
    except:
        messagebox.showerror("Error", "Invalid quantity or money.")
        return

    products = read_csv(PRODUCTS_FILE)
    prod = next((p for p in products if p["ID"] == pid), None)
    if not prod:
        messagebox.showerror("Error", "Product not found.")
        return

    if int(prod["Quantity"]) < qty:
        messagebox.showerror("Error", "Not enough stock.")
        return

    total = float(prod["Price"]) * qty

    # Prevent negative change (money given < total)
    if money < total:
        messagebox.showerror("Error", f"Insufficient amount! Total is ₹{total:.2f}, but you gave ₹{money:.2f}.")
        return

    sid = generate_id(SALES_FILE, "SALE", "Sale_Number")
    change = money - total
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for p in products:
        if p["ID"] == pid:
            p["Quantity"] = str(int(p["Quantity"]) - qty)

    write_csv(PRODUCTS_FILE, products, products[0].keys())

    with open(SALES_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([sid, pid, prod["Name"], qty, total, money, change, method, date])

    messagebox.showinfo("Success", f"💰 Sale recorded!\nChange: ₹{change:.2f}")
    if refresh_callback:
        refresh_callback()

def record_credit_sale(cname, pid, qty, paid, refresh_callback=None):
    if not cname or not pid or not qty or not paid:
        messagebox.showerror("Error", "All fields required.")
        return
    try:
        qty = int(qty)
        paid = float(paid)
    except:
        messagebox.showerror("Error", "Invalid values.")
        return

    prod = next((p for p in read_csv(PRODUCTS_FILE) if p["ID"] == pid), None)
    if not prod:
        messagebox.showerror("Error", "Product not found.")
        return

    total = float(prod["Price"]) * qty
    balance = total - paid
    cid = generate_id(CREDIT_FILE, "CRED", "Credit_ID")
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(CREDIT_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([cid, cname, pid, prod["Name"], qty, total, paid, balance, date])

    messagebox.showinfo("Success", f"🧾 Credit sale recorded!\nBalance: ₹{balance:.2f}")
    if refresh_callback:
        refresh_callback()

def update_credit_payment(credit_id, payment, refresh_callback=None):
    if not credit_id or not payment:
        messagebox.showerror("Error", "Please fill all fields.")
        return

    confirm = messagebox.askyesno("Confirm Update", f"Are you sure you want to update payment for Credit ID '{credit_id}'?")
    if not confirm:
        return

    try:
        payment = float(payment)
    except:
        messagebox.showerror("Error", "Invalid payment amount.")
        return

    credits = read_csv(CREDIT_FILE)
    found = False
    for c in credits:
        if c["Credit_ID"] == credit_id:
            old_paid = float(c["Amount_Paid"])
            new_paid = old_paid + payment
            c["Amount_Paid"] = str(new_paid)
            c["Balance"] = str(float(c["Total_Amount"]) - new_paid)
            found = True
            break

    if not found:
        messagebox.showerror("Error", "Credit record not found.")
        return

    write_csv(CREDIT_FILE, credits, credits[0].keys())
    messagebox.showinfo("Success", "✅ Payment updated successfully!")
    if refresh_callback:
        refresh_callback()

def delete_sale_record(sale_id, refresh_callback=None):
    if not sale_id:
        messagebox.showerror("Error", "Please enter Sale ID.")
        return

    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete Sale Record '{sale_id}'?")
    if not confirm:
        return

    rows = read_csv(SALES_FILE)
    filtered = [r for r in rows if r["Sale_Number"] != sale_id]

    if len(filtered) == len(rows):
        messagebox.showerror("Error", f"Sale ID '{sale_id}' not found.")
        return

    write_csv(SALES_FILE, filtered, rows[0].keys())
    messagebox.showinfo("Deleted", f"🗑 Sale record '{sale_id}' deleted successfully.")
    if refresh_callback:
        refresh_callback()

def delete_credit_record(credit_id, refresh_callback=None):
    if not credit_id:
        messagebox.showerror("Error", "Please enter Credit ID.")
        return

    confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete Credit Record '{credit_id}'?")
    if not confirm:
        return

    rows = read_csv(CREDIT_FILE)
    filtered = [r for r in rows if r["Credit_ID"] != credit_id]

    if len(filtered) == len(rows):
        messagebox.showerror("Error", f"Credit ID '{credit_id}' not found.")
        return

    write_csv(CREDIT_FILE, filtered, rows[0].keys())
    messagebox.showinfo("Deleted", f"🗑 Credit record '{credit_id}' deleted successfully.")
    if refresh_callback:
        refresh_callback()

def modify_credit_record(credit_id, new_name, new_paid, refresh_callback=None):
    if not credit_id:
        messagebox.showerror("Error", "Please enter Credit ID.")
        return

    rows = read_csv(CREDIT_FILE)
    found = False
    for c in rows:
        if c["Credit_ID"] == credit_id:
            if new_name:
                c["Customer_Name"] = new_name
            if new_paid:
                try:
                    new_paid = float(new_paid)
                    c["Amount_Paid"] = str(new_paid)
                    c["Balance"] = str(float(c["Total_Amount"]) - new_paid)
                except:
                    messagebox.showerror("Error", "Invalid payment amount.")
                    return
            found = True
            break

    if not found:
        messagebox.showerror("Error", f"Credit record '{credit_id}' not found.")
        return

    write_csv(CREDIT_FILE, rows, rows[0].keys())
    messagebox.showinfo("Success", f"✅ Credit record '{credit_id}' updated successfully.")
    if refresh_callback:
        refresh_callback()

# ---------------------------
# DISPLAY TABLE UTIL
# ---------------------------
def show_table(frame, file, start_date=None, end_date=None, date_field=None):
    for w in frame.winfo_children():
        w.destroy()

    try:
        df = pd.read_csv(file)
    except Exception as e:
        tk.Label(frame, text=f"No data available ({e})", fg="white", bg="#1e1e1e").pack()
        return

    if start_date or end_date:
        if date_field and date_field in df.columns:
            df[date_field] = pd.to_datetime(df[date_field], errors='coerce')
            if start_date:
                try:
                    s = pd.to_datetime(start_date)
                    df = df[df[date_field] >= s]
                except:
                    pass
            if end_date:
                try:
                    e = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                    df = df[df[date_field] <= e]
                except:
                    pass

    headers = list(df.columns)
    tree = ttk.Treeview(frame, columns=headers, show="headings")

    for h in headers:
        tree.heading(h, text=h)
        tree.column(h, width=120, anchor="center")

    for _, row in df.iterrows():
        values = [row[h] for h in headers]
        tree.insert("", "end", values=values)

    style = ttk.Style()
    style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d", rowheight=28)
    style.map("Treeview", background=[("selected", "#0cc2aa")])

    tree.pack(fill="both", expand=True)
    return tree

# ---------------------------
# REPORT & EXPORT
# ---------------------------

    for w in frame.winfo_children():
        w.destroy()

    if not os.path.exists(SALES_FILE) or os.path.getsize(SALES_FILE) == 0:
        tk.Label(frame, text="No sales data available.", fg="white", bg="#1e1e1e", font=("Segoe UI", 12)).pack()
        return

    try:
        df = pd.read_csv(SALES_FILE)
        df['Sale_Date'] = pd.to_datetime(df['Sale_Date'], errors='coerce')
        df['Month'] = df['Sale_Date'].dt.to_period('M').astype(str)

        # Group by month
        monthly_data = df.groupby('Month').agg({
            'Total_Amount': 'sum',
            'Sale_Number': 'count'
        }).reset_index().rename(columns={'Sale_Number': 'Total_Sales'})

        total_sales = monthly_data['Total_Sales'].sum()
        total_revenue = monthly_data['Total_Amount'].sum()

        tk.Label(frame, text=f"🧾 Total Sales: {total_sales} | 💰 Total Revenue: ₹{total_revenue:,.2f}",
                 bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=10)

        # --- BAR CHART: Total Sales per Month ---
        fig1, ax1 = plt.subplots(figsize=(6, 3))
        ax1.bar(monthly_data['Month'], monthly_data['Total_Sales'])
        ax1.set_title("📦 Total Sales per Month", fontsize=11)
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Number of Sales")
        ax1.tick_params(axis='x', rotation=45)
        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(pady=10)

       

        # --- HORIZONTAL BAR CHART: Top 5 Best-Selling Products ---
        top_products = df.groupby('Product_Name')['Quantity_Sold'].sum().nlargest(5)
        fig3, ax3 = plt.subplots(figsize=(6, 3))
        ax3.barh(top_products.index, top_products.values)
        ax3.set_title("🏆 Top 5 Best-Selling Products", fontsize=11)
        ax3.set_xlabel("Units Sold")
        fig3.tight_layout()
        canvas3 = FigureCanvasTkAgg(fig3, master=frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(pady=10)

        # --- PIE CHART: Revenue Share by Top 5 Products ---
        top_revenue = df.groupby('Product_Name')['Total_Amount'].sum().nlargest(5)
        fig4, ax4 = plt.subplots(figsize=(5, 4))
        wedges, texts, autotexts = ax4.pie(
            top_revenue.values,
            labels=top_revenue.index,
            autopct='%1.1f%%',
            startangle=140,
            textprops={'color': 'white', 'fontsize': 9}
        )
        ax4.set_title("🥧 Top 5 Products by Revenue Share", fontsize=11)
        fig4.patch.set_facecolor('#1e1e1e')
        ax4.set_facecolor('#1e1e1e')
        fig4.tight_layout()
        canvas4 = FigureCanvasTkAgg(fig4, master=frame)
        canvas4.draw()
        canvas4.get_tk_widget().pack(pady=10)

    except Exception as e:
        tk.Label(frame, text=f"Error generating report: {e}", fg="red", bg="#1e1e1e").pack()

    for w in frame.winfo_children():
        w.destroy()

    if not os.path.exists(SALES_FILE) or os.path.getsize(SALES_FILE) == 0:
        tk.Label(frame, text="No sales data available.", fg="white", bg="#1e1e1e", font=("Segoe UI", 12)).pack()
        return

    try:
        df = pd.read_csv(SALES_FILE)
        df['Sale_Date'] = pd.to_datetime(df['Sale_Date'], errors='coerce')
        df['Month'] = df['Sale_Date'].dt.to_period('M').astype(str)

        monthly_data = df.groupby('Month').agg({
            'Total_Amount': 'sum',
            'Sale_Number': 'count'
        }).reset_index().rename(columns={'Sale_Number': 'Total_Sales'})

        total_sales = monthly_data['Total_Sales'].sum()
        total_revenue = monthly_data['Total_Amount'].sum()

        tk.Label(frame, text=f"🧾 Total Sales: {total_sales} | 💰 Total Revenue: ₹{total_revenue:,.2f}",
                 bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=10)

        # chart 1
        fig1, ax1 = plt.subplots(figsize=(6, 3))
        ax1.bar(monthly_data['Month'], monthly_data['Total_Sales'])
        ax1.set_title("📦 Total Sales per Month", fontsize=11)
        ax1.set_xlabel("Month")
        ax1.set_ylabel("Number of Sales")
        ax1.tick_params(axis='x', rotation=45)
        fig1.tight_layout()
        canvas1 = FigureCanvasTkAgg(fig1, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(pady=10)

        # chart 2
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.plot(monthly_data['Month'], monthly_data['Total_Amount'], marker='o')
        ax2.set_title("💸 Monthly Revenue Trend", fontsize=11)
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Revenue (₹)")
        ax2.tick_params(axis='x', rotation=45)
        fig2.tight_layout()
        canvas2 = FigureCanvasTkAgg(fig2, master=frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(pady=10)

        # top products
        top_products = df.groupby('Product_Name')['Quantity_Sold'].sum().nlargest(5)
        fig3, ax3 = plt.subplots(figsize=(6, 3))
        ax3.barh(top_products.index, top_products.values)
        ax3.set_title("🏆 Top 5 Best-Selling Products", fontsize=11)
        ax3.set_xlabel("Units Sold")
        fig3.tight_layout()
        canvas3 = FigureCanvasTkAgg(fig3, master=frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(pady=10)

    except Exception as e:
        tk.Label(frame, text=f"Error generating report: {e}", fg="red", bg="#1e1e1e").pack()
    
        

# ---------------------------
# EXPORT DATA (Improved)
# ---------------------------
def download_csv_gui():
    zip_name = "store_records.zip"
    try:
        with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
            # Add all files inside 'data/' folder dynamically
            for root, _, files in os.walk(DATA_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Keep folder structure clean inside ZIP
                    z.write(file_path, os.path.relpath(file_path, DATA_DIR))
        messagebox.showinfo("Export", f"📦 All data from '{DATA_DIR}/' exported to '{zip_name}' successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export data:\n{e}")


# ---------------------------
# GUI DESIGN & LOGIN
# ---------------------------
def main_gui(username):
    initialize_files()
    root = tk.Tk()
    root.title(f" Sales Management System - User: {username}")
    root.geometry("1200x750")
    root.configure(bg="#1e1e1e")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook", background="#1e1e1e", borderwidth=0)
    style.configure("TNotebook.Tab", padding=[10, 5], background="#333", foreground="white", font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab", background=[("selected", "#0cc2aa")])
    style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#0cc2aa", foreground="white", padding=6)
    style.map("TButton", background=[("active", "#09a899")])

    title = tk.Label(root, text="🛒 Sales Management Dashboard", bg="#0cc2aa", fg="white",
                     font=("Segoe UI", 18, "bold"), pady=15)
    title.pack(fill="x")

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    def labeled_entry(parent, text):
        frame = tk.Frame(parent, bg="#1e1e1e")
        frame.pack(pady=4, anchor="w")
        tk.Label(frame, text=text, fg="white", bg="#1e1e1e", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        entry = tk.Entry(frame, font=("Segoe UI", 10), bg="#333", fg="white", insertbackground="white", width=30)
        entry.pack()
        return entry

    # Refresh helpers
    def refresh_products(): show_table(f4_table, PRODUCTS_FILE)
    def refresh_sales(start=None, end=None): show_table(f5_table, SALES_FILE, start, end, date_field="Sale_Date")
    def refresh_credits(start=None, end=None): show_table(f6_table, CREDIT_FILE, start, end, date_field="Credit_Date")

    # ---------- Add Product ----------
    f1 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f1, text="➕ Add Product")
    name = labeled_entry(f1, "Product Name")
    price = labeled_entry(f1, "Price")
    qty = labeled_entry(f1, "Quantity")
    ttk.Button(f1, text="Add Product", command=lambda: add_product_gui(name.get(), price.get(), qty.get(), refresh_products)).pack(pady=10)

    # ---------- Modify Product ----------
    f2 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f2, text="🧩 Modify Product")
    pid = labeled_entry(f2, "Product ID (e.g., PROD001)")
    nname = labeled_entry(f2, "Name")
    nprice = labeled_entry(f2, "Price")
    nqty = labeled_entry(f2, "Quantity")
    ttk.Button(f2, text="Update Product", command=lambda: modify_product_gui(pid.get(), nname.get(), nprice.get(), nqty.get(), refresh_products)).pack(pady=10)

    # ---------- Record Sale ----------
    f3 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f3, text="💰 Record Sale")
    sid = labeled_entry(f3, "Product ID")
    sqty = labeled_entry(f3, "Quantity Sold")
    smoney = labeled_entry(f3, "Money Given")
    tk.Label(f3, text="Payment Method", fg="white", bg="#1e1e1e", font=("Segoe UI", 10, "bold")).pack(pady=5)
    payment_method = ttk.Combobox(f3, values=["Cash", "UPI"], font=("Segoe UI", 10), state="readonly", width=27)
    payment_method.set("Cash")
    payment_method.pack(pady=5)
    ttk.Button(f3, text="Record Sale", command=lambda: record_sale_gui(sid.get(), sqty.get(), smoney.get(), payment_method.get(), lambda: refresh_sales())).pack(pady=10)

    # ---------- Product List ----------
    f4 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f4, text="📦 Product List")
    f4_table = tk.Frame(f4, bg="#1e1e1e")
    f4_table.pack(fill="both", expand=True)
    show_table(f4_table, PRODUCTS_FILE)

    tk.Label(f4, text="🗑 Delete Product", bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8)
    delete_pid = tk.Entry(f4, font=("Segoe UI", 10), bg="#333", fg="white", insertbackground="white", width=25)
    delete_pid.pack()
    ttk.Button(f4, text="Delete Product", command=lambda: delete_product_gui(delete_pid.get(), lambda: show_table(f4_table, PRODUCTS_FILE))).pack(pady=10)

    # ---------- Sales Records (with Date Filter & Delete) ----------
    f5 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f5, text="📊 Sales Records")
    # filter controls
    filter_frame = tk.Frame(f5, bg="#1e1e1e")
    filter_frame.pack(pady=6, anchor="w")
    tk.Label(filter_frame, text="Start Date (YYYY-MM-DD)", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=6)
    s_start = tk.Entry(filter_frame, bg="#333", fg="white", width=14)
    s_start.grid(row=0, column=1, padx=6)
    tk.Label(filter_frame, text="End Date (YYYY-MM-DD)", bg="#1e1e1e", fg="white").grid(row=0, column=2, padx=6)
    s_end = tk.Entry(filter_frame, bg="#333", fg="white", width=14)
    s_end.grid(row=0, column=3, padx=6)
    ttk.Button(filter_frame, text="Filter", command=lambda: refresh_sales(s_start.get(), s_end.get())).grid(row=0, column=4, padx=6)
    ttk.Button(filter_frame, text="Clear", command=lambda: (s_start.delete(0, 'end'), s_end.delete(0, 'end'), refresh_sales())).grid(row=0, column=5, padx=6)

    f5_table = tk.Frame(f5, bg="#1e1e1e")
    f5_table.pack(fill="both", expand=True)
    show_table(f5_table, SALES_FILE, date_field="Sale_Date")

    tk.Label(f5, text="🗑 Delete Sale Record", bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8)
    delete_id = tk.Entry(f5, font=("Segoe UI", 10), bg="#333", fg="white", insertbackground="white", width=25)
    delete_id.pack()
    ttk.Button(f5, text="Delete Sale", command=lambda: delete_sale_record(delete_id.get(), lambda: refresh_sales())).pack(pady=10)

    # ---------- Credit Sales (scrollable, with date filter, modify & delete) ----------
    f6_container = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f6_container, text="🧾 Credit Sales")

    canvas = tk.Canvas(f6_container, bg="#1e1e1e", highlightthickness=0)
    scrollbar = ttk.Scrollbar(f6_container, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    cname = labeled_entry(scrollable_frame, "Customer Name")
    cpid = labeled_entry(scrollable_frame, "Product ID")
    cqty = labeled_entry(scrollable_frame, "Quantity")
    cpaid = labeled_entry(scrollable_frame, "Amount Paid")
    ttk.Button(scrollable_frame, text="Record Credit Sale", command=lambda: record_credit_sale(cname.get(), cpid.get(), cqty.get(), cpaid.get(), lambda: refresh_credits())).pack(pady=10)

    tk.Label(scrollable_frame, text="Filter Credit Records by Date", bg="#1e1e1e", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=6, anchor="w")
    credit_filter_frame = tk.Frame(scrollable_frame, bg="#1e1e1e")
    credit_filter_frame.pack(anchor="w")
    c_start = tk.Entry(credit_filter_frame, bg="#333", fg="white", width=14)
    c_end = tk.Entry(credit_filter_frame, bg="#333", fg="white", width=14)
    tk.Label(credit_filter_frame, text="Start (YYYY-MM-DD)", bg="#1e1e1e", fg="white").grid(row=0, column=0, padx=6)
    c_start.grid(row=0, column=1, padx=6)
    tk.Label(credit_filter_frame, text="End (YYYY-MM-DD)", bg="#1e1e1e", fg="white").grid(row=0, column=2, padx=6)
    c_end.grid(row=0, column=3, padx=6)
    ttk.Button(credit_filter_frame, text="Filter", command=lambda: refresh_credits(c_start.get(), c_end.get())).grid(row=0, column=4, padx=6)
    ttk.Button(credit_filter_frame, text="Clear", command=lambda: (c_start.delete(0,'end'), c_end.delete(0,'end'), refresh_credits())).grid(row=0, column=5, padx=6)

    tk.Label(scrollable_frame, text="Existing Credit Records:", bg="#1e1e1e", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=5, anchor="w")
    f6_table = tk.Frame(scrollable_frame, bg="#1e1e1e")
    f6_table.pack(fill="both", expand=True)
    show_table(f6_table, CREDIT_FILE, date_field="Credit_Date")

    tk.Label(scrollable_frame, text="💵 Update Payment", bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8, anchor="w")
    cid_entry = labeled_entry(scrollable_frame, "Credit ID (e.g., CRED001)")
    pay_entry = labeled_entry(scrollable_frame, "Payment Amount")
    ttk.Button(scrollable_frame, text="Update Payment", command=lambda: update_credit_payment(cid_entry.get(), pay_entry.get(), lambda: refresh_credits())).pack(pady=10)

    tk.Label(scrollable_frame, text="🧩 Modify Credit Record", bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8, anchor="w")
    mod_cid = labeled_entry(scrollable_frame, "Credit ID (e.g., CRED001)")
    mod_name = labeled_entry(scrollable_frame, "New Customer Name (optional)")
    mod_paid = labeled_entry(scrollable_frame, "New Amount Paid (optional)")
    ttk.Button(scrollable_frame, text="Modify Credit Record", command=lambda: modify_credit_record(mod_cid.get(), mod_name.get(), mod_paid.get(), lambda: refresh_credits())).pack(pady=10)

    tk.Label(scrollable_frame, text="🗑 Delete Credit Record", bg="#1e1e1e", fg="white", font=("Segoe UI", 11, "bold")).pack(pady=8, anchor="w")
    del_cid = labeled_entry(scrollable_frame, "Credit ID to Delete")
    ttk.Button(scrollable_frame, text="Delete Credit Record", command=lambda: delete_credit_record(del_cid.get(), lambda: refresh_credits())).pack(pady=10)

    # ---------- Export ----------
    f7 = tk.Frame(notebook, bg="#1e1e1e")
    notebook.add(f7, text="⬇️ Export")
    tk.Label(f7, text="Export all records to ZIP", bg="#1e1e1e", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=10)
    ttk.Button(f7, text="Download ZIP", command=download_csv_gui).pack()

    

    root.mainloop()

# ---------------------------
# LOGIN WINDOW
# ---------------------------
def login_window():
    initialize_files()
    win = tk.Tk()
    win.title("Login - Store Management")
    win.geometry("420x300")
    win.configure(bg="#1e1e1e")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 10, "bold"))

    tk.Label(win, text="🔐 Login", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=12)

    def labeled(parent, text):
        f = tk.Frame(parent, bg="#1e1e1e")
        f.pack(pady=6)
        tk.Label(f, text=text, bg="#1e1e1e", fg="white").pack(anchor="w")
        e = tk.Entry(f, width=30)
        e.pack()
        return e

    user_entry = labeled(win, "Username")
    pass_entry = labeled(win, "Password")
    pass_entry.config(show="*")

    def do_login():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        if not username or not password:
            messagebox.showerror("Error", "Enter both username and password.")
            return
        users = read_csv(USERS_FILE)
        user = next((u for u in users if u["Username"] == username), None)
        if not user:
            messagebox.showerror("Error", "User not found.")
            return
        if user["PasswordHash"] != sha256(password):
            messagebox.showerror("Error", "Invalid password.")
            return
        # success
        win.destroy()
        main_gui(username)

    ttk.Button(win, text="Login", command=do_login).pack(pady=10)
    ttk.Button(win, text="Create User (admin only)", command=lambda: create_user_window()).pack(pady=4)
    win.mainloop()

def create_user_window():
    # small window to create a user; NOTE: no role verification here - intended for admin use
    w = tk.Toplevel()
    w.title("Create User")
    w.geometry("400x260")
    w.configure(bg="#1e1e1e")

    def labeled(parent, text):
        f = tk.Frame(parent, bg="#1e1e1e")
        f.pack(pady=6)
        tk.Label(f, text=text, bg="#1e1e1e", fg="white").pack(anchor="w")
        e = tk.Entry(f, width=30)
        e.pack()
        return e

    u = labeled(w, "Username")
    p = labeled(w, "Password")
    r = labeled(w, "Role (admin/user)")

    def create_user():
        username = u.get().strip()
        password = p.get().strip()
        role = r.get().strip() or "user"
        if not username or not password:
            messagebox.showerror("Error", "Provide username and password.")
            return
        users = read_csv(USERS_FILE)
        if any(x["Username"] == username for x in users):
            messagebox.showerror("Error", "User already exists.")
            return
        with open(USERS_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([username, sha256(password), role])
        messagebox.showinfo("Success", f"User '{username}' created.")
        w.destroy()

    ttk.Button(w, text="Create", command=create_user).pack(pady=10)
    w.mainloop()

# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    login_window()
