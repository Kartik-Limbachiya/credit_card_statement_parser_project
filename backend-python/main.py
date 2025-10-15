from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from parser import CreditCardStatementParser
import os
import tempfile
import uvicorn

app = FastAPI(
    title="Credit Card Statement Parser API",
    description="Extracts key info from credit card statements (Axis, BOB, Kotak, SBI, Yes Bank)",
    version="1.1.0" # Version updated to reflect new bank support
)

# Production-ready CORS configuration
origins = [
    "http://localhost:3000",  # Allow your local React app
    "http://localhost",
    # Add the URL of your deployed front-end application here
    # Example: "https://your-frontend-app-name.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Initialize the master parser
parser = CreditCardStatementParser()

@app.post("/parse-statement/")
async def parse_statement(bank: str = Form(...), file: UploadFile = File(...)):
    """
    Upload a PDF and specify the bank (axis, bob, kotak, sbi, yes).
    Example: 
        curl -X POST -F "bank=axis" -F "file=@Axis1-unlocked.pdf" https://credit-card-statement-parser.onrender.com/parse-statement/
    """
    # Ensure the uploaded file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Invalid file type. Please upload a PDF."})

    try:
        # Create a temporary file to store the uploaded PDF content
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Parse the PDF using the robust parser
        result = parser.parse_statement(tmp_path, bank)

        return JSONResponse(content=result.to_dict())

    except ValueError as ve:
        # Handle cases where the bank is not supported
        return JSONResponse(status_code=400, content={"error": str(ve)})
    except Exception as e:
        # Handle all other potential errors during parsing
        return JSONResponse(status_code=500, content={"error": f"An unexpected error occurred: {str(e)}"})
    finally:
        # Clean up the temporary file
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/")
async def root():
    """
    Root endpoint with a welcome message and basic usage instructions.
    """
    return {
        "message": "Welcome to the Credit Card Statement Parser API 🚀",
        "usage": "POST to /parse-statement/ with 'bank' and 'file' parameters."
    }


if __name__ == "__main__":
    # Get port from environment variables for deployment flexibility (e.g., on Render)
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)