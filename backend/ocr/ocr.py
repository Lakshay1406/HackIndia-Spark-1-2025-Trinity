import pdfplumber
import pytesseract
import cv2
import numpy as np
from pdf2image import convert_from_path

def extract_text_from_pdf(pdf_path):
    import pdfplumber
    text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # Debugging: Print extracted text
    print(f"\n===== Extracted Text from {pdf_path} =====\n")
    print(text)
    print("\n====================================\n")

    return text.strip()

