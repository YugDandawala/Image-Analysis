"""
Layer 2B: UI Screenshot Grounding Module.

Uses Google Gemini's native spatial grounding capability to detect
interactive UI elements with 2D bounding box coordinates.
Replaces OmniParser v2 — no GPU or local model required.
"""

import json
from pathlib import Path
from google import genai
from google.genai import types
from backend.config import get_settings


UI_GROUNDING_PROMPT = """You are an expert UI/UX analyst. Analyze this screenshot and detect ALL interactive and notable UI elements.

For EACH element, provide:
1. **label**: A descriptive name (e.g., "Login Button", "Search Input Field", "Navigation Menu")
2. **element_type**: One of: button, textbox, dropdown, checkbox, radio, link, image, icon, text, header, navigation, card, modal, menu, slider, toggle, tab, table
3. **box_2d**: Bounding box coordinates as [ymin, xmin, ymax, xmax] normalized to a 0-1000 scale

Also provide a brief **layout_description** summarizing the overall UI layout, structure, and design patterns observed.

Be thorough — detect buttons, input fields, links, navigation elements, cards, images, headers, footers, modals, etc.
Return results as valid JSON matching this exact structure:
{
    "elements": [
        {"label": "...", "element_type": "...", "box_2d": [ymin, xmin, ymax, xmax]},
        ...
    ],
    "layout_description": "..."
}
"""


async def detect_ui_elements(image_path: str) -> dict:
    """Detect UI elements in a screenshot using Gemini spatial grounding.

    Args:
        image_path: Path to the UI screenshot.

    Returns:
        {
            "elements": [{"label": str, "element_type": str, "box_2d": [int, int, int, int]}],
            "layout_description": str,
            "element_count": int,
        }
    """
    settings = get_settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Read image
    image_bytes = Path(image_path).read_bytes()
    mime_type = _get_mime_type(image_path)

    candidate_models = [settings.UI_GROUNDING_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]
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
                            types.Part.from_text(text=UI_GROUNDING_PROMPT),
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                    max_output_tokens=4096,
                ),
            )
            break
        except Exception as e:
            print(f"⚠️ UI grounding model '{model}' failed: {e}. Trying next fallback...")
            continue

    if not response:
        return {"elements": [], "layout_description": "UI element detection quota unavailable.", "element_count": 0}

    # Parse structured response
    try:
        result = json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        text = response.text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {"elements": [], "layout_description": "Could not parse UI elements."}

    elements = result.get("elements", [])
    layout_desc = result.get("layout_description", "")

    return {
        "elements": elements,
        "layout_description": layout_desc,
        "element_count": len(elements),
        "detection_method": "gemini_spatial_grounding",
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
