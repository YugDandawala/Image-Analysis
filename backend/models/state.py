"""
LangGraph pipeline state definition.
This TypedDict defines the full state object that flows through every node in the graph.
"""

from typing import TypedDict, Optional, Any


class PipelineState(TypedDict, total=False):
    """State schema for the LangGraph image analysis pipeline.

    This state object is passed through every node and accumulates
    data as processing progresses through the layers.
    """

    # ── Session & Input ─────────────────────────────────────────────
    session_id: str
    image_path: str                     # Path to the uploaded image on disk
    user_prompt: str                    # The user's question/prompt

    # ── Layer 0: Quality Assessment & Pre-Enhancement ───────────────
    quality_info: Optional[dict[str, Any]] # Quality metrics (blur, resolution, contrast)
    restored_image_path: Optional[str]     # Path to clarity/resolution enhanced image

    # ── Layer 1: Triage Output ──────────────────────────────────────
    category: str                       # medical | ui_screenshot | document | general
    triage_confidence: float            # Classification confidence score

    # ── Layer 2: Module Outputs & Visual Extensions ───────────────
    enhanced_image_path: Optional[str]  # Path to CLAHE-enhanced image (medical)
    annotated_image_path: Optional[str] # Path to bounding box annotated preview image
    annotated_url: Optional[str]        # Web URL for annotated preview
    focus_crop_path: Optional[str]      # Path to 100% native resolution focus crop tile
    sam_segmentation: Optional[dict]    # SAM 2 / OpenCV segmentation polygon data
    verification_report: Optional[dict] # Factual claim verifier output report
    metadata: dict[str, Any]            # Structured data from specialist modules
                                        #   - medical: enhancement params
                                        #   - ui_screenshot: UIElement list
                                        #   - document: Docling markdown + tables
                                        #   - general: basic image info

    # ── Layer 3: Context Assembly ───────────────────────────────────
    assembled_prompt: str               # Final multimodal prompt for VLM

    # ── Layer 4: Master VLM ─────────────────────────────────────────
    system_output: str                  # Final VLM response text

    # ── Conversation ────────────────────────────────────────────────
    chat_history: list[dict[str, str]]  # [{"role": "user"|"assistant", "content": "..."}]

    # ── Pipeline Tracking ───────────────────────────────────────────
    processing_stage: str               # Current stage label for status UI
    completed_stages: list[str]         # List of completed stage names
    error: Optional[str]               # Error message if pipeline fails
