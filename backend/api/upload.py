"""
Image upload endpoint.
Accepts multipart form data, validates, saves, and returns a session ID.
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.models.schemas import UploadResponse
from backend.services.image_service import (
    generate_session_id,
    validate_image_file,
    save_uploaded_image,
    generate_thumbnail,
)
from backend.services.session_manager import session_manager

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="Image file to analyze"),
    prompt: str = Form(default="", description="Initial analysis prompt (optional)"),
):
    """Upload an image for analysis.

    Creates a new session, saves the image, generates a thumbnail,
    and returns the session ID for subsequent chat interactions.
    """
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    filename = file.filename or "unknown.png"

    # Validate
    is_valid, error_msg = validate_image_file(filename, file_size)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Create session
    session_id = generate_session_id()

    # Save image
    image_path = await save_uploaded_image(session_id, filename, file_content)

    # Generate thumbnail
    thumbnail_path = generate_thumbnail(image_path, session_id)

    # Register session
    session = session_manager.create_session(
        session_id=session_id,
        image_path=str(image_path),
        original_filename=filename,
    )

    # If an initial prompt was provided, store it
    if prompt.strip():
        session.add_message("user", prompt.strip())

    return UploadResponse(
        session_id=session_id,
        thumbnail_url=f"/temp/{session_id}/thumbnail.webp",
        original_filename=filename,
    )
