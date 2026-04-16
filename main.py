from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai
import json
import re
import os
import base64
import io
from dotenv import load_dotenv

# DOCX
from docx import Document

# Excel
import pandas as pd

# Load env
load_dotenv()

app = FastAPI()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash-lite")


# -----------------------
# Helpers
# -----------------------

def clean_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        return json.loads(text)
    except Exception as e:
        return {"raw": text, "error": str(e)}


def read_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    return "\n".join([p.text for p in doc.paragraphs])


def read_excel(file_bytes):
    df = pd.read_excel(io.BytesIO(file_bytes))
    return df.to_string()


# -----------------------
# Routes
# -----------------------

@app.get("/")
def home():
    return {"status": "API working 🚀"}


@app.post("/extract-bill")
async def extract_bill(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        file_type = file.content_type

        prompt = """
        You are an expert document parser.

        Extract:
        - Name
        - Provider
        - Due Date
        - Amount

        Rules:
        - Return ONLY JSON
        - If value missing, return empty string
        - Do not add extra text

        Output:
        {
          "name": "",
          "provider": "",
          "due_date": "",
          "amount": ""
        }
        """

        # -----------------------
        # DOCX Handling
        # -----------------------
        if "wordprocessingml.document" in file_type:
            text_content = read_docx(file_bytes)

            response = model.generate_content([
                prompt,
                text_content
            ])

        # -----------------------
        # Excel Handling
        # -----------------------
        elif "spreadsheet" in file_type or "excel" in file_type:
            text_content = read_excel(file_bytes)

            response = model.generate_content([
                prompt,
                text_content
            ])

        # -----------------------
        # PDF & Images
        # -----------------------
        else:
            file_base64 = base64.b64encode(file_bytes).decode("utf-8")

            response = model.generate_content([
                prompt,
                {
                    "mime_type": file_type,
                    "data": file_base64
                }
            ])

        # -----------------------
        # Clean response
        # -----------------------
        result = clean_json(response.text)

        return {
            "success": True,
            "data": result,
            "error": None
        }

    except Exception as e:
        print("ERROR:", str(e))

        return {
            "success": False,
            "data": None,
            "error": str(e)
        }