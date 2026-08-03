"""
Layer 2D: General Image Module — Pass-through with basic optimization.

Handles everyday photographs (nature, people, objects, animals).
No heavy preprocessing — just EXIF orientation fix and optional downscaling.
"""

from pathlib import Path
from PIL import Image
from backend.services.image_service import fix_exif_orientation, downscale_if_needed


async def process_general_image(image_path: str) -> dict:
    """Process a general image with minimal preprocessing.

    Args:
        image_path: Path to the image file.

    Returns:
        {
            "image_info": dict,     # Basic image properties
            "description": str,
        }
    """
    path = Path(image_path)

    # Get basic image info
    with Image.open(path) as img:
        width, height = img.size
        mode = img.mode
        img_format = img.format or path.suffix.upper().replace(".", "")

    # Downscale if oversized (for efficiency with VLM)
    processed_path = downscale_if_needed(path, max_dimension=2048)

    # Get processed dimensions
    if processed_path != path:
        with Image.open(processed_path) as img:
            proc_width, proc_height = img.size
        was_resized = True
    else:
        proc_width, proc_height = width, height
        was_resized = False

    return {
        "image_info": {
            "original_dimensions": (width, height),
            "processed_dimensions": (proc_width, proc_height),
            "format": img_format,
            "color_mode": mode,
            "was_resized": was_resized,
        },
        "processed_image_path": str(processed_path),
        "description": (
            f"General image ({img_format}, {width}x{height}). "
            f"{'Downscaled for processing.' if was_resized else 'No resizing needed.'}"
        ),
    }
