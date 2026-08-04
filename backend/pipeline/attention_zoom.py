"""
High-Resolution Attention Zoom Crop Engine.

Identifies the highest-density or smallest-text region of interest (ROI) inside an image,
crops a 512x512 tile at 100% native resolution (without downscaling blur), and provides
a dual-view payload to the Master VLM.
"""

import cv2
from pathlib import Path
from backend.config import get_settings


def generate_attention_zoom(
    image_path: str,
    session_id: str,
    elements: list[dict] = None,
    target_crop_size: int = 512,
) -> dict:
    """Extract a 100% native resolution focus crop tile.

    Args:
        image_path: Path to original image.
        session_id: Active session identifier.
        elements: List of detected elements (optional focus center).
        target_crop_size: Crop box width/height in pixels.

    Returns:
        {
            "focus_crop_path": str,
            "focus_crop_url": str,
            "crop_center": tuple[int, int],
            "crop_dimensions": tuple[int, int],
        }
    """
    settings = get_settings()

    img = cv2.imread(image_path)
    if img is None:
        return {"focus_crop_path": None, "focus_crop_url": None}

    h, w = img.shape[:2]

    # Default focus center: image center
    center_x, center_y = w // 2, h // 2

    # If elements exist, pick the element with the smallest area (highest density / fine text)
    if elements:
        smallest_area = float("inf")
        for elem in elements:
            box = elem.get("box_2d") or elem.get("bbox")
            if box and len(box) == 4:
                ymin, xmin, ymax, xmax = box
                area = (ymax - ymin) * (xmax - xmin)
                if 0 < area < smallest_area:
                    smallest_area = area
                    center_x = int(((xmin + xmax) / 2000) * w)
                    center_y = int(((ymin + ymax) / 2000) * h)

    # Compute bounding crop box around center
    half_size = target_crop_size // 2
    crop_xmin = max(0, center_x - half_size)
    crop_ymin = max(0, center_y - half_size)
    crop_xmax = min(w, crop_xmin + target_crop_size)
    crop_ymax = min(h, crop_ymin + target_crop_size)

    crop = img[crop_ymin:crop_ymax, crop_xmin:crop_xmax]

    # Save focus crop tile
    output_dir = settings.upload_path / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    crop_path = output_dir / "focus_crop.png"
    cv2.imwrite(str(crop_path), crop)

    return {
        "focus_crop_path": str(crop_path),
        "focus_crop_url": f"/temp/{session_id}/focus_crop.png",
        "crop_center": (center_x, center_y),
        "crop_dimensions": (crop_xmax - crop_xmin, crop_ymax - crop_ymin),
        "description": "High-resolution native scale focus crop tile for localized attention reasoning.",
    }
