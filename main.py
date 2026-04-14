from fastapi import FastAPI, UploadFile, File
import google.generativeai as genai
import json
import re
import os
import base64

app = FastAPI()

# ✅ Use ENV variable (Render)
# genai.configure(api_key=os.getenv("AIzaSyD1J76PmPgt-xIsTF4KATEJ_zEwH5tZMNU"))
os.getenv("AIzaSyD1J76PmPgt-xIsTF4KATEJ_zEwH5tZMNU")

model = genai.GenerativeModel("gemini-2.5-flash")


def clean_json(text):
    try:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)

        return json.loads(text)
    except Exception as e:
        return {"raw": text, "error": str(e)}


@app.post("/extract-bill")
async def extract_bill(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()

        # ✅ Convert to base64 (IMPORTANT FIX)
        file_base64 = base64.b64encode(file_bytes).decode("utf-8")

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
                    "data": file_base64   # ✅ FIXED
                }
            ]
        )

        result = clean_json(response.text)

        return {
            "success": True,
            "data": result,
            "error": None
        }

    except Exception as e:
        print("ERROR:", str(e))  # 👈 check in Render logs

        return {
            "success": False,
            "data": None,
            "error": str(e)
        }