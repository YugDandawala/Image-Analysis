"""
Annotated Visual Overlay Generator.

Draws color-coded 2D bounding boxes, semantic labels, and segmentation boundaries
directly onto the original image using OpenCV. Generates an annotated preview image
file (`annotated_preview.png`) that can be rendered in the frontend UI.
"""

import cv2
import numpy as np
from pathlib import Path
from backend.config import get_settings


# Category-specific color palettes (BGR format)
PALETTE = {
    "button": (255, 128, 0),       # Bright blue-orange
    "textbox": (0, 204, 102),      # Emerald green
    "dropdown": (204, 0, 204),     # Magenta
    "header": (0, 153, 255),       # Amber yellow
    "navigation": (255, 51, 153),  # Deep violet
    "card": (128, 128, 128),       # Medium gray
    "table": (0, 102, 204),        # Dark orange
    "text": (51, 153, 255),        # Golden yellow
    "default": (0, 255, 255),     # Yellow-cyan
}


def generate_visual_overlay(
    image_path: str,
    session_id: str,
    elements: list[dict],
    polygons: list[list[int]] = None,
    category: str = "general",
) -> dict:
    """Draw semi-transparent bounding boxes and badges on the image.

    Args:
        image_path: Path to original image.
        session_id: Session ID for output storage.
        elements: List of UI/Document elements with box_2d [ymin, xmin, ymax, xmax] (0-1000 scale).
        polygons: Optional list of additional segmentation polygons.
        category: Image domain category.

    Returns:
        {
            "annotated_image_path": str,
            "annotated_url": str,
            "element_count": int,
        }
    """
    settings = get_settings()

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image for overlay generation: {image_path}")

    h, w = img.shape[:2]
    overlay = img.copy()

    # Draw SAM / OpenCV segmentation contours if provided
    if polygons:
        for box in polygons[:10]:
            if len(box) == 4:
                ymin, xmin, ymax, xmax = box
                pt1 = (int((xmin / 1000) * w), int((ymin / 1000) * h))
                pt2 = (int((xmax / 1000) * w), int((ymax / 1000) * h))
                cv2.rectangle(overlay, pt1, pt2, (200, 200, 250), 1, cv2.LINE_AA)

    # Draw detected interactive elements with color coding
    count = 0
    for elem in elements:
        box = elem.get("box_2d") or elem.get("bbox")
        if not box or len(box) != 4:
            continue

        ymin, xmin, ymax, xmax = box
        px_xmin = int((xmin / 1000) * w)
        px_ymin = int((ymin / 1000) * h)
        px_xmax = int((xmax / 1000) * w)
        px_ymax = int((ymax / 1000) * h)

        elem_type = str(elem.get("element_type") or elem.get("type") or "default").lower()
        color = PALETTE.get(elem_type, PALETTE["default"])

        # Filled semi-transparent bounding box
        cv2.rectangle(overlay, (px_xmin, px_ymin), (px_xmax, px_ymax), color, -1)
        # Bounding border
        cv2.rectangle(img, (px_xmin, px_ymin), (px_xmax, px_ymax), color, 2, cv2.LINE_AA)

        # Label badge text
        label = elem.get("label") or elem_type.upper()
        if len(label) > 25:
            label = label[:22] + "..."

        # Draw label background badge
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        badge_w, badge_h = text_size[0] + 8, text_size[1] + 6
        badge_ymin = max(0, px_ymin - badge_h)

        cv2.rectangle(img, (px_xmin, badge_ymin), (px_xmin + badge_w, badge_ymin + badge_h), color, -1)
        cv2.putText(
            img,
            label,
            (px_xmin + 4, badge_ymin + badge_h - 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        count += 1

    # Blend semi-transparent fill layer (alpha = 0.25)
    final = cv2.addWeighted(overlay, 0.25, img, 0.75, 0)

    # Save output image
    output_dir = settings.upload_path / session_id
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = output_dir / "annotated_preview.png"
    cv2.imwrite(str(annotated_path), final)

    return {
        "annotated_image_path": str(annotated_path),
        "annotated_url": f"/temp/{session_id}/annotated_preview.png",
        "element_count": count,
    }
