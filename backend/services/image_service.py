"""
Image handling service: file saving, thumbnail generation, validation.
"""

import uuid
import os
from pathlib import Path
from PIL import Image, ExifTags
from io import BytesIO
from backend.config import get_settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp", ".gif"}
THUMBNAIL_SIZE = (300, 300)


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return uuid.uuid4().hex[:16]


def validate_image_file(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate uploaded file type and size.

    Returns:
        (is_valid, error_message)
    """
    settings = get_settings()

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    if file_size > settings.max_image_bytes:
        return False, f"File too large ({file_size / 1024 / 1024:.1f}MB). Max: {settings.MAX_IMAGE_SIZE_MB}MB"

    return True, ""


def get_session_dir(session_id: str) -> Path:
    """Get or create a session-specific directory inside the upload folder."""
    settings = get_settings()
    session_dir = settings.upload_path / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


async def save_uploaded_image(session_id: str, filename: str, file_content: bytes) -> Path:
    """Save uploaded image to the session directory.

    Returns:
        Path to the saved image file.
    """
    session_dir = get_session_dir(session_id)
    ext = Path(filename).suffix.lower()
    save_path = session_dir / f"original{ext}"

    with open(save_path, "wb") as f:
        f.write(file_content)

    return save_path


def fix_exif_orientation(image: Image.Image) -> Image.Image:
    """Auto-rotate image based on EXIF orientation tag."""
    try:
        exif = image._getexif()
        if exif is None:
            return image

        orientation_key = None
        for key, val in ExifTags.TAGS.items():
            if val == "Orientation":
                orientation_key = key
                break

        if orientation_key is None or orientation_key not in exif:
            return image

        orientation = exif[orientation_key]
        rotations = {
            3: 180,
            6: 270,
            8: 90,
        }
        if orientation in rotations:
            image = image.rotate(rotations[orientation], expand=True)

    except (AttributeError, KeyError, IndexError):
        pass

    return image


def generate_thumbnail(image_path: Path, session_id: str) -> Path:
    """Generate a thumbnail for the uploaded image.

    Returns:
        Path to the thumbnail file.
    """
    session_dir = get_session_dir(session_id)
    thumb_path = session_dir / "thumbnail.webp"

    with Image.open(image_path) as img:
        img = fix_exif_orientation(img)
        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        img.save(thumb_path, format="WEBP", quality=85)

    return thumb_path


def downscale_if_needed(image_path: Path, max_dimension: int = 2048) -> Path:
    """Downscale image if any dimension exceeds max_dimension.

    Returns:
        Path to the (possibly resized) image.
    """
    with Image.open(image_path) as img:
        width, height = img.size
        if width <= max_dimension and height <= max_dimension:
            return image_path

        # Calculate new dimensions preserving aspect ratio
        ratio = min(max_dimension / width, max_dimension / height)
        new_size = (int(width * ratio), int(height * ratio))

        img = img.resize(new_size, Image.Resampling.LANCZOS)
        resized_path = image_path.parent / f"resized_{image_path.name}"
        img.save(resized_path)
        return resized_path
