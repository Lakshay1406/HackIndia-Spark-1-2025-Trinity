import re

def parse_invoice(text):
    print("\n✅ Starting Invoice Parsing...")  # Debugging
    data = {
        "Invoice Number": "N/A",
        "Order Number": "N/A",
        "From": "N/A",
        "Invoice Date": "N/A",
        "Product Name / Service": "N/A",
        "Quantity (Hrs/Qty)": "N/A",
        "Rate/Price": "N/A",
        "Sub Total": "N/A"
    }

    print("\n🔍 Extracting Invoice Metadata...")  # Debugging
    invoice_match = re.search(r"Invoice Number\s*(INV-\d+)", text, re.IGNORECASE)
    order_match = re.search(r"Order Number\s*(\d+)", text, re.IGNORECASE)
    date_match = re.search(r"Invoice Date\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.IGNORECASE)

    print("\n🔍 Extracting 'From' Section...")  # Debugging
    from_match = re.search(r"From:\s*(.+?)\nTo:", text, re.DOTALL | re.IGNORECASE)
    if from_match:
        data["From"] = from_match.group(1).strip().replace("\n", " ")

    print("\n🔍 Extracting Table Data...")  # Debugging
    lines = text.split("\n")
    inside_table = False
    current_product = ""
    quantities = []
    products = []
    rates = []
    subtotals = []

    for i, line in enumerate(lines):
        line = line.strip()

        # Ignore empty lines and OCR noise
        if not line or len(line) == 1:
            continue  

        # Detect Table Start
        if re.search(r"Hrs/Qty\s+Service\s+Rate/Price\s+Adjust\s+Sub Total", line, re.IGNORECASE):
            inside_table = True
            continue  # Skip header line

        # Stop at "Sub Total" row
        if inside_table and "Sub Total" in line:
            inside_table = False
            continue

        if inside_table:
            print(f"🔹 Processing Row: {line}")  # Debugging

            # If line is only text, it's part of a service name (multi-line support)
            if not re.search(r"\d+\.\d{2}", line):  
                current_product = line.strip()
                continue  

            # If line contains numbers (likely quantity, price, subtotal)
            parts = re.split(r'\s+', line)  

            if len(parts) >= 4:
                quantity = parts[0].strip()
                rate = parts[-3].strip()
                subtotal = parts[-1].strip()

                # Merge with previously stored product name
                products.append(current_product)
                quantities.append(quantity)
                rates.append("$" + rate)
                subtotals.append("$" + subtotal)

    # Save Extracted Values
    data["Quantity (Hrs/Qty)"] = ", ".join(quantities) if quantities else "N/A"
    data["Product Name / Service"] = ", ".join(products) if products else "N/A"
    data["Rate/Price"] = ", ".join(rates) if rates else "N/A"
    data["Sub Total"] = ", ".join(subtotals) if subtotals else "N/A"

    # Extract matched values
    data["Invoice Number"] = invoice_match.group(1) if invoice_match else "N/A"
    data["Order Number"] = order_match.group(1) if order_match else "N/A"
    data["Invoice Date"] = date_match.group(1) if date_match else "N/A"

    print(f"\n✅ Final Parsed Data:\n{data}\n=====================")  # Debugging output
    return data
