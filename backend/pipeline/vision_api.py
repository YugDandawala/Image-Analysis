"""
Meta SAM 2 & DINOv2 Feature Extraction Module.

Interfaces with Hugging Face Inference API / Replicate for SAM 2 zero-shot segmentation
and DINOv2 visual feature representations.

Includes robust fallback to OpenCV adaptive contour segmentation and structural feature
extraction if API keys are omitted or network calls fail.
"""

import json
import urllib.request
import urllib.error
import cv2
import numpy as np
from pathlib import Path
from backend.config import get_settings


async def extract_sam2_segmentation(image_path: str) -> dict:
    """Extract zero-shot object/region segmentation masks using SAM 2 or OpenCV fallback.

    Args:
        image_path: Path to the image file on disk.

    Returns:
        {
            "mask_count": int,
            "polygons": list[list[list[int]]],
            "method": str,
            "description": str,
        }
    """
    settings = get_settings()

    # Try Hugging Face API if key is provided
    if settings.HUGGINGFACE_API_KEY:
        try:
            return await _extract_sam2_hf_api(image_path, settings.HUGGINGFACE_API_KEY)
        except Exception as e:
            print(f"⚠️ SAM2 HF API call failed ({e}). Using OpenCV adaptive segmentation fallback.")

    # Graceful fallback: OpenCV Adaptive Segmentation
    return _extract_sam2_fallback(image_path)


async def extract_dinov2_features(image_path: str) -> dict:
    """Extract self-supervised visual feature embedding metrics using DINOv2 or fallback.

    Args:
        image_path: Path to the image file.

    Returns:
        {
            "feature_dim": int,
            "structural_density": float,
            "edge_complexity": float,
            "method": str,
        }
    """
    settings = get_settings()

    # Try Hugging Face API if key is provided
    if settings.HUGGINGFACE_API_KEY:
        try:
            return await _extract_dinov2_hf_api(image_path, settings.HUGGINGFACE_API_KEY)
        except Exception as e:
            print(f"⚠️ DINOv2 HF API call failed ({e}). Using OpenCV structural feature fallback.")

    # Fallback structural feature metrics
    return _extract_dinov2_fallback(image_path)


async def _extract_sam2_hf_api(image_path: str, api_key: str) -> dict:
    """Call Hugging Face Inference API for SAM 2 / Segmentation."""
    settings = get_settings()
    url = f"https://api-inference.huggingface.co/models/{settings.SAM2_MODEL_ID}"

    image_bytes = Path(image_path).read_bytes()
    req = urllib.request.Request(
        url,
        data=image_bytes,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=8) as response:
        res_bytes = response.read()
        res_json = json.loads(res_bytes.decode("utf-8"))

    masks = res_json if isinstance(res_json, list) else []
    return {
        "mask_count": len(masks),
        "masks": masks[:10],
        "method": "meta_sam2_hf_api",
        "description": f"Extracted {len(masks)} object segmentations via Meta SAM 2 API.",
    }


async def _extract_dinov2_hf_api(image_path: str, api_key: str) -> dict:
    """Call Hugging Face Inference API for DINOv2 embeddings."""
    settings = get_settings()
    url = f"https://api-inference.huggingface.co/models/{settings.DINOV2_MODEL_ID}"

    image_bytes = Path(image_path).read_bytes()
    req = urllib.request.Request(
        url,
        data=image_bytes,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/octet-stream",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=8) as response:
        res_bytes = response.read()
        res_json = json.loads(res_bytes.decode("utf-8"))

    return {
        "feature_dim": 768,
        "raw_embedding_summary": str(res_json)[:200],
        "method": "meta_dinov2_hf_api",
        "description": "Dense self-supervised visual representation extracted via Meta DINOv2 API.",
    }


def _extract_sam2_fallback(image_path: str) -> dict:
    """OpenCV contour adaptive segmentation fallback."""
    img = cv2.imread(image_path)
    if img is None:
        return {"mask_count": 0, "polygons": [], "method": "opencv_fallback"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    valid_polygons = []
    h, w = img.shape[:2]
    min_area = (h * w) * 0.005  # At least 0.5% of total area

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            x, y, cw, ch = cv2.boundingRect(cnt)
            # Normalized box_2d [ymin, xmin, ymax, xmax] in 0-1000 scale
            ymin, xmin = int((y / h) * 1000), int((x / w) * 1000)
            ymax, xmax = int(((y + ch) / h) * 1000), int(((x + cw) / w) * 1000)
            valid_polygons.append([ymin, xmin, ymax, xmax])

    return {
        "mask_count": len(valid_polygons),
        "polygons": valid_polygons[:15],
        "method": "opencv_adaptive_segmentation",
        "description": f"Extracted {len(valid_polygons)} spatial segmentation boundaries.",
    }


def _extract_dinov2_fallback(image_path: str) -> dict:
    """OpenCV structural visual density metric fallback."""
    img = cv2.imread(image_path)
    if img is None:
        return {"feature_dim": 0, "structural_density": 0.0, "edge_complexity": 0.0, "method": "opencv_fallback"}

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    edge_ratio = float(np.count_nonzero(edges) / edges.size)
    std_dev = float(gray.std())

    return {
        "feature_dim": 512,
        "structural_density": round(std_dev, 2),
        "edge_complexity": round(edge_ratio, 4),
        "method": "opencv_structural_feature_analysis",
        "description": "Visual structure analyzed via edge density and spatial variance analysis.",
    }
