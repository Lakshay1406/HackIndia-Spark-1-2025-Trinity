# -----------------------------------------------
#        Integrate Gemini for SQL Queries
# -----------------------------------------------
import sqlite3
import pandas as pd
import google.generativeai as genai
import os
import json
import time
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini API Key
genai.configure(api_key=api_key)

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change "*" to your frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)
# api_key = os.getenv("GOOGLE_API_KEY")
# file_loc = os.getenv("file_loc")
# Configure Gemini API Key
# genai.configure(api_key=api_key)
def sql_query(query: str):
    """Run a SQL SELECT query on a SQLite database and return the results."""
    with sqlite3.connect("invoice_data.db") as connection:
        print(query)
        return pd.read_sql_query(query, connection).to_dict(orient="records")
    


system_prompt = """
NO SQL should be retruned as ans always call sql_query function to get the results.
Only give results by querying the database and the give back only the result recieved after quering. Do not make up any information.
When you generate a query, use the 'sql_query' function to execute the query on the database and get the results.
Then, use the results to answer the user's question
You are an expert SQL analyst. When appropriate, generate SQL queries based on the user’s question and make them case insensitive and the database schema.
When you generate a query, use the 'sql_query' function to execute the query on the database and get the results.
Then, use the results to answer the user's question.

### Database Schema:
1. **invoices**  
   - invoice_no (TEXT, PRIMARY KEY)  
   - purchase_order_no (TEXT)  
   - issued_date (TEXT)  
   - supplier_code (TEXT)  
   - invoice_received_date (TEXT)  
   - invoice_due_date (TEXT)  
   - product_name (TEXT)  
   - quantity (INTEGER)  
   - total_cost (REAL)  

2. **purchase_orders**  
   - purchase_order_no (TEXT, PRIMARY KEY)  
   - purchase_issued_date (TEXT)  
   - supplier_code (TEXT)  
   - product_name (TEXT)  
   - quantity (INTEGER)  
   - total_cost (REAL)  

3. **reference_table** (Dispute Summary)  
   - invoice_no (TEXT, FOREIGN KEY referencing invoices(invoice_no))  
   - purchase_order_no (TEXT, FOREIGN KEY referencing purchase_orders(purchase_order_no))  
   - dispute (TEXT CHECK(dispute IN ('YES', 'NO')))  -- Ensures only 'Yes' or 'No'  
   - dispute_type (TEXT)  -- 'Rate', 'Quantity', or NULL if no dispute  
   - product_disputed (TEXT)  -- Lists product names with issues  

### Query Execution Rules:
- Always use the `sql_query` function to execute queries.
- If an invoice has a dispute, set `dispute = 'Yes'`, otherwise `dispute = 'No'`.
- If the quantity or cost does not match, set `dispute_type = 'Quantity'` or `dispute_type = 'Rate'` accordingly.
- If there are multiple products with mismatches, store them in `product_disputed` as a comma-separated string.
- Ensure that all joins between tables are correctly executed to retrieve matching purchase orders.

""".strip()

# Configure Gemini Model
sql_gemini = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=system_prompt,
    tools=[sql_query]
)
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str  # Ensures the request body must contain a 'message' field as a string

chat = sql_gemini.start_chat(enable_automatic_function_calling=True)
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handles chatbot messages via a simple POST request."""
    
    response = chat.send_message(request.message)

    # Convert response to JSON format
    return {"response": response.text}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get script directory
UPLOAD_DIR = os.path.join(BASE_DIR, "/ocrFolder/input/")
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import os
from uuid import uuid4
import os
# Create the upload directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/file/")
async def upload_file(file: UploadFile = File(...)):
    # Generate a unique filename
    filename = f"{uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # Return the filename or URL to access the file
    file_url = f"http://127.0.0.1:8000/files/{filename}"
    
    return {"file_url": file_url}

@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Check if the file exists and return it
    if os.path.exists(file_path):
        return FileResponse(file_path)
    
    return {"message": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
