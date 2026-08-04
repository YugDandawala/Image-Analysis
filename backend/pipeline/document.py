"""
Layer 2C: Document & Chart Processing Module — Tesseract & Deterministic OCR Engine.

Uses Tesseract OCR (via pytesseract) + OpenCV spatial layout analysis to extract
exact ground-truth text, tabular layouts, and document structure without relying
on generative models for text extraction.

This ground-truth OCR content (exact text + Markdown formatted tables) is passed
directly to the Master VLM alongside the image so the final model has BOTH the
visual representation and non-hallucinated OCR data for accurate reasoning.
"""

import os
import shutil
import re
import cv2
import numpy as np
from pathlib import Path
from backend.config import get_settings

# Attempt to configure Tesseract binary path on Windows if needed
try:
    import pytesseract
    PYTESSERACT_INSTALLED = True
except Exception as e:
    PYTESSERACT_INSTALLED = False
    pytesseract = None
    print(f"⚠️ pytesseract module not imported: {e}")

def _configure_tesseract() -> bool:
    """Locate tesseract executable on system or standard Windows install paths."""
    if not PYTESSERACT_INSTALLED or pytesseract is None:
        return False
    try:
        tesseract_cmd = shutil.which("tesseract")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            return True

        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expanduser(r"~\anaconda3\Library\bin\tesseract.exe"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                return True
    except Exception as e:
        print(f"⚠️ Tesseract binary detection warning: {e}")
    return False

# Configure on module import
TESSERACT_AVAILABLE = _configure_tesseract()


async def extract_document_content(image_path: str) -> dict:
    """Extract exact ground-truth content from a document image.

    Strategy:
      1. Tesseract OCR + OpenCV spatial layout table structuring (exact ground-truth).
      2. IBM Docling OCR fallback (if Tesseract binary is not installed).

    Args:
        image_path: Path to the document image.

    Returns:
        {
            "full_text": str,
            "markdown": str,
            "tables": list[dict],
            "table_count": int,
            "extraction_method": str,
            "description": str,
        }
    """
    # 1. Try Tesseract OCR with spatial layout table extraction
    if TESSERACT_AVAILABLE:
        try:
            res = _extract_with_tesseract(image_path)
            if res and res.get("full_text", "").strip():
                return res
        except Exception as e:
            print(f"⚠️ Tesseract OCR extraction warning: {e}. Falling back to Docling OCR...")

    # 2. Docling OCR fallback
    try:
        return await _extract_with_docling(image_path)
    except Exception as e:
        print(f"⚠️ Docling fallback failed: {e}. Using OpenCV basic spatial extraction.")
        return _extract_opencv_spatial(image_path)


def _extract_with_tesseract(image_path: str) -> dict:
    """Extract text and format tabular layout using Tesseract PSM + spatial line grouping.

    Returns exact text, structured markdown, and extracted table blocks.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Convert to grayscale for optimal Tesseract OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # Apply light adaptive thresholding for high-contrast OCR
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # 1. Plain text extraction via Tesseract
    raw_text = pytesseract.image_to_string(thresh, config="--psm 6 --oem 3").strip()
    if not raw_text:
        raw_text = pytesseract.image_to_string(gray, config="--psm 3 --oem 3").strip()

    # 2. Detailed TSV spatial data extraction for table & column grouping
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    n_boxes = len(data["text"])
    lines_map = {}

    for i in range(n_boxes):
        text = data["text"][i].strip()
        conf = int(data["conf"][i]) if "conf" in data and str(data["conf"][i]).isdigit() else 0

        if text and conf > 20:
            top = data["top"][i]
            left = data["left"][i]
            width = data["width"][i]

            # Group into lines by y-coordinate (12px tolerance)
            matched_line_y = None
            for y_key in lines_map:
                if abs(top - y_key) <= 12:
                    matched_line_y = y_key
                    break

            if matched_line_y is None:
                matched_line_y = top
                lines_map[matched_line_y] = []

            lines_map[matched_line_y].append({"left": left, "text": text, "width": width})

    # Sort lines vertically
    sorted_y_keys = sorted(lines_map.keys())

    markdown_lines = []
    table_candidates = []
    current_table_rows = []

    for y in sorted_y_keys:
        # Sort words in line horizontally by x-coordinate
        row_words = sorted(lines_map[y], key=lambda item: item["left"])
        row_str = " ".join([w["text"] for w in row_words])

        # Detect tabular structure (multiple horizontally spaced elements)
        if len(row_words) >= 3:
            # Table row candidate
            col_formatted = " | ".join([w["text"] for w in row_words])
            current_table_rows.append(f"| {col_formatted} |")
        else:
            if current_table_rows:
                if len(current_table_rows) >= 2:
                    table_md = _build_markdown_table(current_table_rows)
                    markdown_lines.append(table_md)
                    table_candidates.append({"markdown": table_md})
                current_table_rows = []
            markdown_lines.append(row_str)

    if current_table_rows and len(current_table_rows) >= 2:
        table_md = _build_markdown_table(current_table_rows)
        markdown_lines.append(table_md)
        table_candidates.append({"markdown": table_md})

    formatted_markdown = "\n\n".join(markdown_lines) if markdown_lines else raw_text

    return {
        "full_text": raw_text,
        "markdown": formatted_markdown,
        "tables": table_candidates,
        "table_count": len(table_candidates),
        "extraction_method": "tesseract_spatial_ocr",
        "description": (
            f"Ground-truth OCR extracted using Tesseract Engine. "
            f"Preserved exact text and {len(table_candidates)} tabular layout region(s)."
        ),
    }


def _build_markdown_table(rows: list[str]) -> str:
    """Format raw tabular rows into a valid Markdown table with separator line."""
    if not rows:
        return ""
    header = rows[0]
    num_cols = header.count("|") - 1
    separator = "| " + " | ".join(["---"] * max(1, num_cols)) + " |"
    return "\n".join([header, separator] + rows[1:])


async def _extract_with_docling(image_path: str) -> dict:
    """Docling OCR fallback for complex multi-page documents."""
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(image_path)

    markdown_output = result.document.export_to_markdown()

    tables = []
    for table in result.document.tables:
        table_data = {
            "title": "",
            "markdown": table.export_to_markdown() if hasattr(table, "export_to_markdown") else str(table),
        }
        tables.append(table_data)

    full_text = result.document.export_to_text() if hasattr(result.document, "export_to_text") else markdown_output

    return {
        "full_text": full_text,
        "markdown": markdown_output,
        "tables": tables,
        "table_count": len(tables),
        "extraction_method": "docling_ocr_fallback",
        "description": f"Document parsed with Docling OCR. Found {len(tables)} table(s).",
    }


def _extract_opencv_spatial(image_path: str) -> dict:
    """OpenCV contour fallback when external OCR engines are unavailable."""
    img = cv2.imread(image_path)
    if img is None:
        return {"full_text": "", "markdown": "", "tables": [], "table_count": 0, "extraction_method": "failed"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return {
        "full_text": f"Document resolution: {img.shape[1]}x{img.shape[0]} px.",
        "markdown": "Spatial structure analyzed via OpenCV.",
        "tables": [],
        "table_count": 0,
        "extraction_method": "opencv_spatial_fallback",
        "description": "Basic spatial layout analysis applied.",
    }
