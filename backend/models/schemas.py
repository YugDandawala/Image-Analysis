"""
Pydantic schemas for API request/response models.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Upload ──────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response returned after a successful image upload."""
    session_id: str = Field(..., description="Unique session identifier")
    thumbnail_url: str = Field(..., description="URL to the generated thumbnail")
    original_filename: str = Field(..., description="Original uploaded filename")
    message: str = "Image uploaded successfully"


# ── Chat ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    session_id: str = Field(..., description="Session ID from upload")
    message: str = Field(..., min_length=1, description="User's question or prompt")


class ChatResponse(BaseModel):
    """Non-streaming chat response."""
    session_id: str
    response: str
    category: Optional[str] = None
    processing_stages: Optional[list[str]] = None


# ── Pipeline Status ─────────────────────────────────────────────────

class PipelineStatusResponse(BaseModel):
    """Current pipeline processing status for a session."""
    session_id: str
    current_stage: str = Field(..., description="Current processing stage name")
    completed_stages: list[str] = Field(default_factory=list)
    is_complete: bool = False
    category: Optional[str] = None
    error: Optional[str] = None


# ── UI Element Detection (Layer 2B) ────────────────────────────────

class UIElement(BaseModel):
    """A single detected UI element with bounding box."""
    label: str = Field(..., description="Element label, e.g. 'Login Button'")
    element_type: str = Field(..., description="Type: button, textbox, dropdown, image, link, text, icon, etc.")
    box_2d: list[int] = Field(..., description="Bounding box [ymin, xmin, ymax, xmax] in 0-1000 scale")


class UIAnalysisResult(BaseModel):
    """Structured result from UI grounding analysis."""
    elements: list[UIElement] = Field(default_factory=list)
    layout_description: str = Field(default="", description="Brief description of the overall UI layout")


# ── Health Check ────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    pipeline_ready: bool = True
