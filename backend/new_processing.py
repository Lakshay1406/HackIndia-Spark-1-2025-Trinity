import pandas as pd
import sqlite3
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
api_key = os.getenv("GOOGLE_API_KEY")
# api_key = os.getenv("GOOGLE_API_KEY")
# file_loc = os.getenv("file_loc")
# Configure Gemini API Key
genai.configure(api_key=api_key)

# Load Excel file (update filename accordingly)
excel_file = "ocr.xlsx"

# Load sheets into pandas DataFrames
invoices_df = pd.read_excel(excel_file, sheet_name="Sheet1")  # Now 'invoices'
purchase_orders_df = pd.read_excel(excel_file, sheet_name="Sheet2")  # Now 'purchase_orders'

# Rename columns for consistency
invoices_df.rename(columns={
    "Invoice No.": "invoice_no",
    "purchase order no.": "purchase_order_no",
    "Issued date": "issued_date",
    "supplier Code": "supplier_code",
    "Invoice received date": "invoice_received_date",
    "Invoice Due date": "invoice_due_date",
    "product name": "product_name",
    "quantity": "quantity",
    "total cost": "total_cost"
}, inplace=True)

purchase_orders_df.rename(columns={
    "purchase order no.": "purchase_order_no",
    "purchase Issued date": "purchase_issued_date",
    "supplier Code": "supplier_code",
    "product name": "product_name",
    "quantity": "quantity",
    "total cost": "total_cost"
}, inplace=True)

# Connect to SQLite database
conn = sqlite3.connect("invoice_data.db")
cursor = conn.cursor()

# Drop existing tables (if they exist)
cursor.executescript("""
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS purchase_orders;
DROP TABLE IF EXISTS reference_table;

CREATE TABLE invoices (
    invoice_no TEXT,
    purchase_order_no TEXT,
    issued_date TEXT,
    supplier_code TEXT,
    invoice_received_date TEXT,
    invoice_due_date TEXT,
    product_name TEXT,
    quantity INTEGER,
    total_cost REAL
);

CREATE TABLE purchase_orders (
    purchase_order_no TEXT,
    purchase_issued_date TEXT,
    supplier_code TEXT,
    product_name TEXT,
    quantity INTEGER,
    total_cost REAL
);

CREATE TABLE reference_table (
    invoice_no TEXT,
    purchase_order_no TEXT,
    dispute TEXT,
    dispute_type TEXT,
    product_disputed TEXT
);
""")

# Insert data into tables
invoices_df.to_sql("invoices", conn, if_exists="append", index=False)
purchase_orders_df.to_sql("purchase_orders", conn, if_exists="append", index=False)

# Process invoices and purchase orders
invoice_po_combinations = invoices_df[['invoice_no', 'purchase_order_no']].drop_duplicates()

for _, row in invoice_po_combinations.iterrows():
    invoice_no = row['invoice_no']
    po_no = row['purchase_order_no']
    
    # Get products from both tables
    invoice_products = invoices_df[invoices_df['purchase_order_no'] == po_no]
    po_products = purchase_orders_df[purchase_orders_df['purchase_order_no'] == po_no]
    
    disputes = []
    dispute_type_set = set()
    
    for _, product_row in invoice_products.iterrows():
        product_name = product_row['product_name']
        invoice_quantity = product_row['quantity']
        invoice_total_cost = product_row['total_cost']

        match = po_products[po_products['product_name'] == product_name]

        if match.empty:
            disputes.append(product_name)
            dispute_type_set.add("Missing")
        else:
            po_quantity = match.iloc[0]['quantity']
            po_total_cost = match.iloc[0]['total_cost']

            if invoice_quantity != po_quantity:
                disputes.append(product_name)
                dispute_type_set.add("Quantity")
            if invoice_total_cost != po_total_cost:
                disputes.append(product_name)
                dispute_type_set.add("Rate")

    dispute_status = "YES" if disputes else "NO"
    dispute_type = ", ".join(dispute_type_set) if dispute_type_set else None
    disputed_products = ", ".join(set(disputes)) if disputes else None

    # Insert into reference table
    cursor.execute("""
        INSERT INTO reference_table (invoice_no, purchase_order_no, dispute, dispute_type, product_disputed)
        VALUES (?, ?, ?, ?, ?)
    """, (invoice_no, po_no, dispute_status, dispute_type, disputed_products))

# Commit and close connection
conn.commit()
conn.close()

print("Database tables created successfully!")

