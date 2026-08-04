"""
Image Quality Assessment & Non-Generative Resolution/Clarity Restoration.

Inspects incoming images for blurriness, low-resolution, and dull contrast.
Applies mathematical signal processing techniques (Laplacian variance detection,
Bicubic/Lanczos anti-aliased upscaling, Bilateral edge-preserving filtering,
Unsharp Masking, and LAB CLAHE luminance tuning) to produce a sharp, high-clarity image
without using generative AI or synthetic image creation models.
"""

import cv2
import numpy as np
from pathlib import Path
from backend.config import get_settings


async def analyze_image_quality(image_path: str) -> dict:
    """Analyze image quality parameters: blur variance, resolution, contrast.

    Args:
        image_path: Path to the original image on disk.

    Returns:
        {
            "laplacian_var": float,
            "dimensions": tuple[int, int],
            "std_dev": float,
            "is_blurry": bool,
            "is_low_res": bool,
            "is_low_contrast": bool,
            "needs_enhancement": bool,
        }
    """
    settings = get_settings()

    img = cv2.imread(image_path)
    if img is None:
        return {
            "laplacian_var": 0.0,
            "dimensions": (0, 0),
            "std_dev": 0.0,
            "is_blurry": False,
            "is_low_res": False,
            "is_low_contrast": False,
            "needs_enhancement": False,
        }

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    std_dev = float(gray.std())

    is_blurry = laplacian_var < settings.BLUR_THRESHOLD
    is_low_res = min(h, w) < settings.MIN_DIMENSION_THRESHOLD
    is_low_contrast = std_dev < 40.0

    needs_enhancement = (is_blurry or is_low_res or is_low_contrast) and settings.AUTO_ENHANCE_QUALITY

    return {
        "laplacian_var": round(laplacian_var, 2),
        "dimensions": (w, h),
        "std_dev": round(std_dev, 2),
        "is_blurry": is_blurry,
        "is_low_res": is_low_res,
        "is_low_contrast": is_low_contrast,
        "needs_enhancement": needs_enhancement,
    }


async def enhance_image_clarity(image_path: str, session_id: str, quality_info: dict) -> dict:
    """Fix image blur, low resolution, and poor contrast using classical signal processing.

    Args:
        image_path: Path to original image.
        session_id: Active session ID for saving output.
        quality_info: Result dict from analyze_image_quality.

    Returns:
        {
            "restored_image_path": str,
            "applied_fixes": list[str],
            "initial_quality": dict,
            "post_quality": dict,
        }
    """
    settings = get_settings()
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image for enhancement: {image_path}")

    enhanced = img.copy()
    h, w = enhanced.shape[:2]
    applied_fixes = []

    # 1. Anti-aliased Upscaling for Low-Resolution Images
    if quality_info.get("is_low_res"):
        scale_factor = 1.5 if min(h, w) > 500 else 2.0
        new_w, new_h = int(w * scale_factor), int(h * scale_factor)
        enhanced = cv2.resize(enhanced, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        applied_fixes.append(f"Resized resolution from {w}x{h} to {new_w}x{new_h} via Bicubic interpolation")

    # 2. Denoising using Bilateral Filter (preserves sharp edges)
    enhanced = cv2.bilateralFilter(enhanced, d=5, sigmaColor=35, sigmaSpace=35)
    applied_fixes.append("Applied edge-preserving bilateral denoising filter")

    # 3. Unsharp Masking (USM) for Blur Fix & Edge Sharpening
    if quality_info.get("is_blurry") or True:
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=3.0)
        enhanced = cv2.addWeighted(enhanced, 1.6, gaussian, -0.6, 0)
        applied_fixes.append("Applied Unsharp Masking (USM) edge sharpening to eliminate blur")

    # 4. Dynamic Contrast Tuning via LAB Color Space CLAHE
    if quality_info.get("is_low_contrast"):
        if len(enhanced.shape) == 3:
            lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            enhanced = cv2.cvtColor(cv2.merge((l_clahe, a, b)), cv2.COLOR_LAB2BGR)
        else:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(enhanced)
        applied_fixes.append("Enhanced luminance contrast range via LAB CLAHE")

    # Save restored image
    output_dir = settings.upload_path / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    restored_path = output_dir / "enhanced_clarity.png"
    cv2.imwrite(str(restored_path), enhanced)

    # Post-enhancement quality check
    post_gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY) if len(enhanced.shape) == 3 else enhanced
    post_lap = float(cv2.Laplacian(post_gray, cv2.CV_64F).var())

    return {
        "restored_image_path": str(restored_path),
        "applied_fixes": applied_fixes,
        "initial_laplacian_var": quality_info.get("laplacian_var"),
        "post_laplacian_var": round(post_lap, 2),
        "description": "Image quality restored using non-generative signal processing and unsharp masking.",
    }
