"""
Handles uploaded bill files: PDFs and images.
When a Gemini API key is configured, it sends the file content to Gemini for extraction.
"""

import io
import json
import base64
from pathlib import Path
from typing import Optional


def read_uploaded_file(uploaded_file) -> tuple[str, bytes]:
    """
    Read a Streamlit uploaded file.
    Returns (mime_type, raw_bytes).
    """
    file_bytes = uploaded_file.read()
    name = uploaded_file.name.lower()

    if name.endswith(".pdf"):
        mime = "application/pdf"
    elif name.endswith((".jpg", ".jpeg")):
        mime = "image/jpeg"
    elif name.endswith(".png"):
        mime = "image/png"
    elif name.endswith(".webp"):
        mime = "image/webp"
    else:
        mime = "application/octet-stream"

    return mime, file_bytes


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Attempt plain-text extraction from a PDF using PyPDF2.
    Returns extracted text or empty string if extraction fails or yields nothing useful.
    """
    try:
        import PyPDF2

        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        return "\n".join(text_parts)
    except Exception:
        return ""


def parse_bill_with_gemini(
    file_bytes: bytes,
    mime_type: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> Optional[list[dict]]:
    """
    Send the bill image/PDF to Google Gemini and extract structured line items.

    Returns a list of dicts with keys:
        name, category, quantity, unit, unit_rate, amount
    or None if parsing failed.
    """
    try:
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel(model)

        prompt = """You are an expert medical bill analyst for Indian hospitals.

Analyze this hospital bill image/document and extract ALL line items.

For EACH line item return a JSON object with exactly these fields:
- "name": descriptive item name (string)
- "category": one of ["Room Charges", "Doctor Fees", "Diagnostics", "Procedures", "OT & Anesthesia", "Medicines", "Consumables", "Nursing Services", "Administrative", "Other"]
- "quantity": numeric quantity (number, default 1 if not stated)
- "unit": unit of measurement (string, e.g. "days", "tablets", "tests", "vials", "pieces", "procedure", "visit")
- "unit_rate": rate per unit in INR (number)
- "amount": total amount in INR (number)

Return ONLY a valid JSON array like:
[
  {"name": "Private Room", "category": "Room Charges", "quantity": 3, "unit": "days", "unit_rate": 5000, "amount": 15000},
  ...
]

Rules:
- Extract every single line item, do not skip any
- If quantity is not shown, set quantity to 1 and unit_rate = amount
- All amounts must be numbers (not strings), without commas or currency symbols
- Do not include totals, sub-totals, taxes, or discounts as separate items
- If you cannot extract structured data, return an empty array []
"""

        # Build the content parts
        if mime_type == "application/pdf":
            # Convert PDF bytes to base64 for inline data
            b64 = base64.standard_b64encode(file_bytes).decode()
            content = [
                prompt,
                {
                    "inline_data": {
                        "mime_type": "application/pdf",
                        "data": b64,
                    }
                },
            ]
        else:
            # Image file
            from PIL import Image

            img = Image.open(io.BytesIO(file_bytes))
            content = [prompt, img]

        safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }

        response = gemini_model.generate_content(
            content, safety_settings=safety_settings
        )
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(
                l for l in lines if not l.strip().startswith("```")
            )

        items = json.loads(raw)

        # Validate and clean each item
        cleaned = []
        for item in items:
            try:
                cleaned.append(
                    {
                        "name": str(item.get("name", "Unknown Item")).strip(),
                        "category": str(
                            item.get("category", "Other")
                        ).strip(),
                        "quantity": float(item.get("quantity", 1)),
                        "unit": str(item.get("unit", "each")).strip(),
                        "unit_rate": float(item.get("unit_rate", 0)),
                        "amount": float(item.get("amount", 0)),
                    }
                )
            except (ValueError, TypeError):
                continue

        return cleaned if cleaned else None

    except json.JSONDecodeError:
        return None
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}") from e
