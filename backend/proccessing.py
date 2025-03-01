import sqlite3
import pandas as pd
def process_invoices_and_po():
    # Connect to SQLite database
    conn = sqlite3.connect("invoice_data.db")
    cursor = conn.cursor()

    # Fetch invoices and purchase orders from the database
    invoices_df = pd.read_sql_query("SELECT * FROM invoices", conn)
    purchase_orders_df = pd.read_sql_query("SELECT * FROM purchase_orders", conn)

    # Get unique invoice and PO combinations
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

    print("Processing completed and reference table updated!")

