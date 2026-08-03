"""
Layer 2C: Document & Chart Processing Module.

Uses IBM Docling for structured document parsing, table extraction,
and OCR. Outputs clean Markdown and structured table data.
Falls back to basic OCR if Docling fails.
"""

import json
from pathlib import Path
from backend.config import get_settings


async def extract_document_content(image_path: str) -> dict:
    """Extract structured content from a document image.

    Uses IBM Docling for layout analysis, table structure recognition,
    and OCR extraction. Falls back gracefully if Docling is unavailable.

    Args:
        image_path: Path to the document image.

    Returns:
        {
            "full_text": str,           # Complete extracted text
            "markdown": str,            # Markdown-formatted output
            "tables": list[dict],       # Extracted tables
            "extraction_method": str,
        }
    """
    try:
        return await _extract_with_docling(image_path)
    except Exception as e:
        print(f"⚠️ Docling extraction failed: {e}. Using fallback OCR.")
        return await _extract_fallback(image_path)


async def _extract_with_docling(image_path: str) -> dict:
    """Extract content using IBM Docling."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(image_path)

    # Export to markdown
    markdown_output = result.document.export_to_markdown()

    # Extract tables if present
    tables = []
    for table in result.document.tables:
        table_data = {
            "markdown": table.export_to_markdown() if hasattr(table, "export_to_markdown") else str(table),
        }
        tables.append(table_data)

    # Get plain text
    full_text = result.document.export_to_text() if hasattr(result.document, "export_to_text") else markdown_output

    return {
        "full_text": full_text,
        "markdown": markdown_output,
        "tables": tables,
        "table_count": len(tables),
        "extraction_method": "docling",
        "description": (
            f"Document parsed with IBM Docling. "
            f"Extracted {len(tables)} table(s) and structured text content."
        ),
    }


async def _extract_fallback(image_path: str) -> dict:
    """Fallback extraction using basic image-to-text via Gemini.

    If Docling is not installed or fails, we use Gemini to extract
    text content from the document image.
    """
    from google import genai
    from google.genai import types

    settings = get_settings()
    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    image_bytes = Path(image_path).read_bytes()
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".tiff": "image/tiff", ".tif": "image/tiff",
        ".bmp": "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")

    candidate_models = [settings.MASTER_VLM_MODEL, "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.6-flash"]
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
                            types.Part.from_text(
                                text=(
                                    "Extract ALL text from this document image. "
                                    "Preserve the layout as closely as possible. "
                                    "If there are tables, format them as Markdown tables. "
                                    "Output only the extracted content, no commentary."
                                )
                            ),
                            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                ),
            )
            break
        except Exception as e:
            print(f"⚠️ Document OCR model '{model}' failed: {e}. Trying next fallback...")
            continue

    extracted_text = response.text.strip() if response else "Document text extraction limit exceeded."

    return {
        "full_text": extracted_text,
        "markdown": extracted_text,
        "tables": [],
        "table_count": 0,
        "extraction_method": "gemini_fallback",
        "description": "Document text extracted using Gemini VLM fallback (Docling unavailable).",
    }
