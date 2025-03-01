import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
def invoice_ocr_data_cleaner():
    # Connect to SQLite database
    db_path = "invoice_data.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Load Excel file with OCR extracted data
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory

    excel_path = BASE_DIR+"/ocrFolder/output/invoices.xlsx"
    df = pd.read_excel(excel_path)

    # Function to format invoice number
    def format_invoice_no(invoice_no):
        return invoice_no.replace("INV-", "INV")  # Remove "-"

    # Function to format PO Number
    def format_po_no(order_no):
        return f"PO{order_no}"  # Add "PO" prefix

    # Function to convert date formats
    def convert_date(date_str):
        try:
            return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None  # If date parsing fails, return None

    # Function to get supplier code
    def get_supplier_code(supplier_name):
        query = "SELECT code FROM supplier_details WHERE supplier_name = ?"
        cursor.execute(query, (supplier_name,))
        result = cursor.fetchone()
        return result[0] if result else "UNKNOWN"  # Default to UNKNOWN if not found

    # Invoice received date is today
    today_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Invoice due date is 30 days from today
    due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

    # Clean and transform data
    df_transformed = pd.DataFrame()
    df_transformed["invoice_no"] = df["Invoice Number"].apply(format_invoice_no)
    df_transformed["purchase_order_no"] = df["Order Number"].apply(format_po_no)
    df_transformed["issued_date"] = df["Invoice Date"].apply(convert_date)
    df_transformed["supplier_code"] = df["From"].apply(get_supplier_code)
    df_transformed["invoice_received_date"] = today_date
    df_transformed["invoice_due_date"] = due_date
    df_transformed["product_name"] = df["Product Name / Service"]
    df_transformed["quantity"] = df["Quantity (Hrs/Qty)"]
    df_transformed["total_cost"] = df["Sub Total"].replace(r"[$,]", "", regex=True).astype(float)  # Remove "$" and convert to number

    # Push cleaned data into SQLite database
    df_transformed.to_sql("invoices", conn, if_exists="append", index=False)

    # Close connection
    conn.commit()
    conn.close()
    try:
        os.remove(excel_path)
        print(f"File '{excel_path}' has been deleted successfully.")
    except Exception as e:
        print(f"Error deleting file '{excel_path}': {e}")

    print("Data successfully inserted into the database.")
