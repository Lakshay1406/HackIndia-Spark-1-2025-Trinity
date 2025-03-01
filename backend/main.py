#first move the received invoice to input folder and then run the main.py file to process the invoices.
from ocrFolder.main import process_invoices
from proccessing import process_invoices_and_po
from invoice_cleaner import invoice_ocr_data_cleaner

if __name__ == "__main__":
    process_invoices()
    invoice_ocr_data_cleaner()
    process_invoices_and_po()