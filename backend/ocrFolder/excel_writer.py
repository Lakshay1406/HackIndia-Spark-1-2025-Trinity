import pandas as pd
import os


def write_to_excel(data):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
    OUTPUT_FILE = BASE_DIR+"/output/invoices.xlsx"

    df = pd.DataFrame([data])

    # Check if the Excel file exists
    if os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_excel(OUTPUT_FILE, engine="openpyxl")
        final_df = pd.concat([existing_df, df], ignore_index=True)
    else:
        final_df = df

    # Save to Excel
    final_df.to_excel(OUTPUT_FILE, index=False, engine="openpyxl")

    print("\n✅ Data successfully written to Excel!\n")
