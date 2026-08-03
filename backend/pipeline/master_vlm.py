"""
Layer 4: Master Synthesis VLM — Final Conversational Reasoning.

Invokes Gemini 3.5 Flash with the assembled context prompt and
attached image(s) to generate the final grounded, conversational response.
"""

from pathlib import Path
from google import genai
from google.genai import types
from backend.config import get_settings


async def generate_response(
    assembled_prompt: str,
    image_path: str,
    enhanced_image_path: str = None,
) -> str:
    """Generate the final conversational response from the Master VLM.

    Args:
        assembled_prompt: The fully assembled context prompt from Layer 3.
        image_path: Path to the original image.
        enhanced_image_path: Optional path to an enhanced image (medical).

    Returns:
        The VLM's response text.
    """
    settings = get_settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Build content parts
    parts = [types.Part.from_text(text=assembled_prompt)]

    # Attach original image
    original_bytes = Path(image_path).read_bytes()
    original_mime = _get_mime_type(image_path)
    parts.append(types.Part.from_bytes(data=original_bytes, mime_type=original_mime))

    # Attach enhanced image if available (medical scans)
    if enhanced_image_path and Path(enhanced_image_path).exists():
        enhanced_bytes = Path(enhanced_image_path).read_bytes()
        enhanced_mime = _get_mime_type(enhanced_image_path)
        parts.append(types.Part.from_bytes(data=enhanced_bytes, mime_type=enhanced_mime))

    candidate_models = [settings.MASTER_VLM_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    last_exception = None
    for model in models_to_try:
        try:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(role="user", parts=parts)
                ],
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                    top_p=0.95,
                ),
            )
            return response.text
        except Exception as e:
            last_exception = e
            print(f"⚠️ Model '{model}' failed: {e}. Trying next fallback candidate...")
            continue

    raise last_exception


async def generate_followup_response(
    user_message: str,
    image_path: str,
    metadata: dict,
    enhanced_image_path: str = None,
    category: str = "general",
    chat_history: list[dict] = None,
) -> str:
    """Generate a follow-up response without re-running the full pipeline.

    Uses cached metadata from the initial analysis to provide context.

    Args:
        user_message: The follow-up question.
        image_path: Path to the original image.
        metadata: Cached structured metadata from the initial analysis.
        enhanced_image_path: Optional enhanced image path.
        category: Image domain category.
        chat_history: Previous conversation messages.

    Returns:
        The VLM's response text.
    """
    from backend.pipeline.context_assembly import build_assembled_prompt

    # Build context from cached data
    assembled = build_assembled_prompt(
        category=category,
        user_prompt=user_message,
        metadata=metadata,
        chat_history=chat_history or [],
    )

    return await generate_response(
        assembled_prompt=assembled,
        image_path=image_path,
        enhanced_image_path=enhanced_image_path,
    )


def _get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = Path(file_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".gif": "image/gif", ".bmp": "image/bmp",
        ".tiff": "image/tiff", ".tif": "image/tiff",
    }
    return mime_map.get(ext, "image/jpeg")
