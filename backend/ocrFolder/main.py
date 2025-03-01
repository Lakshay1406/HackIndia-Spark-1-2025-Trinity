import os
from ocr.ocr import extract_text_from_pdf



def process_invoices():
    from ocrFolder.parser import parse_invoice
    from ocrFolder.excel_writer import write_to_excel
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
    INPUT_FOLDER = os.path.join(BASE_DIR, "input/")
    # INPUT_FOLDER="input/"
    for filename in os.listdir(INPUT_FOLDER):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(INPUT_FOLDER, filename)
            print(f"Processing: {filename}")

            # Extract text
            text = extract_text_from_pdf(pdf_path)
            print("\n==== Extracted Text ====\n")
            print(text)  # DEBUG: Print extracted text
            print("\n========================\n")

            # Parse invoice data
            invoice_data = parse_invoice(text)

            # Write to Excel
            write_to_excel(invoice_data)

            print(f"Successfully processed {filename}\n")

if __name__ == "__main__":
    process_invoices()
