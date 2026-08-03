"""
Layer 1: Triage Dispatcher — Image Domain Classifier.

Uses Gemini 3.5 Flash-Lite to classify an uploaded image into one of
four categories: medical, ui_screenshot, document, or general.
"""

import base64
from pathlib import Path
from google import genai
from google.genai import types
from backend.config import get_settings

# Categories the triage system can return
VALID_CATEGORIES = {"medical", "ui_screenshot", "document", "general"}

TRIAGE_SYSTEM_PROMPT = """You are an expert image classification system. Your task is to classify the given image into EXACTLY ONE of these categories:

- **medical**: X-rays, CT scans, MRI scans, ultrasound images, dental X-rays, mammograms, any medical/clinical imaging
- **ui_screenshot**: Screenshots of software, websites, mobile apps, dashboards, desktop applications, dialog boxes, any user interface
- **document**: PDFs, invoices, receipts, research papers, letters, forms, charts, graphs, tables, spreadsheets, any text-heavy document
- **general**: Nature photographs, people, animals, objects, food, landscapes, everyday photographs that don't fit the above

RULES:
1. Respond with ONLY the category name (one word), nothing else.
2. If the image contains a chart/graph embedded in a document, classify as "document".
3. If the image shows a medical app's UI, classify as "ui_screenshot".
4. If unsure between categories, pick the most specific one.
"""


async def classify_image(image_path: str) -> dict:
    """Classify an image into a domain category.

    Args:
        image_path: Path to the image file on disk.

    Returns:
        {"category": str, "confidence": float}
    """
    settings = get_settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Read and encode image
    image_bytes = Path(image_path).read_bytes()
    mime_type = _get_mime_type(image_path)

    candidate_models = [settings.TRIAGE_MODEL, "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    response = None
    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text="Classify this image into one category."),
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=TRIAGE_SYSTEM_PROMPT,
                    max_output_tokens=20,
                    temperature=0.1,
                ),
            )
            break
        except Exception as e:
            print(f"⚠️ Triage model '{model}' failed: {e}. Trying next fallback...")
            continue

    if not response:
        return {"category": "general", "confidence": 0.5}

    # Parse response
    raw_category = response.text.strip().lower().replace(" ", "_")

    # Validate category
    if raw_category not in VALID_CATEGORIES:
        # Try to find closest match
        for cat in VALID_CATEGORIES:
            if cat in raw_category or raw_category in cat:
                raw_category = cat
                break
        else:
            raw_category = "general"  # Fallback

    return {
        "category": raw_category,
        "confidence": 0.95 if raw_category != "general" else 0.7,
    }


def _get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")
