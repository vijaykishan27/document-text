from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai
import json
import re

app = FastAPI()

# Configure API Key
genai.configure(api_key="AIzaSyD1J76PmPgt-xIsTF4KATEJ_zEwH5tZMNU")

model = genai.GenerativeModel("gemini-2.5-flash-lite")


def clean_json(text):
    try:
        # Extract JSON part only
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)
    except Exception as e:
        return {"raw": text, "error": str(e)}


@app.post("/extract-bill")
async def extract_bill(file: UploadFile = File(...)):

    file_bytes = await file.read()

    prompt = """
    You are an expert document parser.

    Extract:
    - Name
    - Provider
    - Due Date
    - Amount

    Return ONLY JSON:
    {
      "name": "",
      "provider": "",
      "due_date": "",
      "amount": ""
    }
    """

    response = model.generate_content(
        [
            prompt,
            {
                "mime_type": file.content_type,
                "data": file_bytes
            }
        ]
    )

    result = clean_json(response.text)

    return {"data": result}