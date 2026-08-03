"""
Layer 2A: Medical Imaging Module — CLAHE Enhancement.

Converts medical scans to grayscale and applies CLAHE (Contrast Limited
Adaptive Histogram Equalization) to enhance subtle anatomical structures.
Supports X-rays, CT, MRI, and ultrasound images.
"""

import cv2
import numpy as np
from pathlib import Path
from backend.config import get_settings


async def enhance_medical_image(image_path: str, session_id: str) -> dict:
    """Apply CLAHE enhancement to a medical image.

    Args:
        image_path: Path to the original medical image.
        session_id: Session ID for saving the enhanced image.

    Returns:
        {
            "enhanced_image_path": str,
            "enhancement_params": dict,
            "original_dimensions": tuple,
        }
    """
    settings = get_settings()

    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    original_h, original_w = img.shape[:2]

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter for noise reduction while preserving edges
    denoised = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # Create and apply CLAHE
    clahe = cv2.createCLAHE(
        clipLimit=settings.CLAHE_CLIP_LIMIT,
        tileGridSize=(settings.CLAHE_GRID_SIZE, settings.CLAHE_GRID_SIZE),
    )
    enhanced = clahe.apply(denoised)

    # Save enhanced image
    output_dir = settings.upload_path / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    enhanced_path = output_dir / "enhanced_medical.png"
    cv2.imwrite(str(enhanced_path), enhanced)

    return {
        "enhanced_image_path": str(enhanced_path),
        "enhancement_params": {
            "method": "CLAHE",
            "clip_limit": settings.CLAHE_CLIP_LIMIT,
            "grid_size": settings.CLAHE_GRID_SIZE,
            "bilateral_filter": True,
            "grayscale_converted": True,
        },
        "original_dimensions": (original_w, original_h),
        "description": (
            "Medical image enhanced with CLAHE (Contrast Limited Adaptive "
            "Histogram Equalization). Grayscale conversion applied. Bilateral "
            "filtering used for noise reduction while preserving edge structures."
        ),
    }
