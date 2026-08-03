"""
LangGraph Pipeline Graph — Stateful Workflow Orchestration.

Defines the complete image analysis state machine with conditional
routing based on image category. Nodes:
    triage → medical|ui_grounding|document|general → context_assembly → master_vlm

Follow-up questions bypass the full graph and go directly to the VLM.
"""

import asyncio
from typing import AsyncGenerator
from backend.models.state import PipelineState
from backend.pipeline.triage import classify_image
from backend.pipeline.medical import enhance_medical_image
from backend.pipeline.ui_grounding import detect_ui_elements
from backend.pipeline.document import extract_document_content
from backend.pipeline.general import process_general_image
from backend.pipeline.context_assembly import build_assembled_prompt
from backend.pipeline.master_vlm import generate_response, generate_followup_response
from backend.services.session_manager import session_manager


# ── Pipeline Execution ──────────────────────────────────────────────

async def run_pipeline(
    session_id: str,
    user_prompt: str,
    image_path: str,
) -> AsyncGenerator[dict, None]:
    """Run the full image analysis pipeline with stage-by-stage SSE events.

    Yields SSE event dicts:
        {"type": "stage", "stage": "Stage Name"}
        {"type": "token", "content": "..."}
        {"type": "result", "category": "...", "metadata": {...}}

    Args:
        session_id: Active session identifier.
        user_prompt: The user's question about the image.
        image_path: Path to the uploaded image.
    """
    session = session_manager.get_session(session_id)
    metadata = {}
    enhanced_image_path = None

    # ── Layer 1: Triage ─────────────────────────────────────────────
    yield {"type": "stage", "stage": "Identifying image domain"}
    try:
        triage_result = await classify_image(image_path)
        category = triage_result["category"]
        confidence = triage_result["confidence"]
    except Exception as e:
        category = "general"
        confidence = 0.5
        yield {"type": "stage", "stage": "Classification fallback applied"}

    category_labels = {"medical": "Medical scan", "ui_screenshot": "UI screenshot", "document": "Document", "general": "Photograph"}
    yield {"type": "stage", "stage": f"Detected: {category_labels.get(category, category)}"}

    # ── Layer 2: Specialist Processing ──────────────────────────────
    if category == "medical":
        yield {"type": "stage", "stage": "Enhancing scan contrast"}
        try:
            med_result = await enhance_medical_image(image_path, session_id)
            metadata = med_result
            enhanced_image_path = med_result.get("enhanced_image_path")
        except Exception as e:
            metadata = {"error": str(e), "description": "Medical enhancement failed."}
            yield {"type": "stage", "stage": "Enhancement completed with warnings"}

    elif category == "ui_screenshot":
        yield {"type": "stage", "stage": "Detecting interface elements"}
        try:
            ui_result = await detect_ui_elements(image_path)
            metadata = ui_result
        except Exception as e:
            metadata = {"error": str(e), "elements": [], "layout_description": "UI detection failed."}
            yield {"type": "stage", "stage": "Detection completed with warnings"}

    elif category == "document":
        yield {"type": "stage", "stage": "Extracting text and structure"}
        try:
            doc_result = await extract_document_content(image_path)
            metadata = doc_result
        except Exception as e:
            metadata = {"error": str(e), "full_text": "", "markdown": "", "tables": []}
            yield {"type": "stage", "stage": "Extraction completed with warnings"}

    elif category == "general":
        yield {"type": "stage", "stage": "Processing image content"}
        try:
            gen_result = await process_general_image(image_path)
            metadata = gen_result
        except Exception as e:
            metadata = {"error": str(e), "description": "General processing failed."}

    # ── Layer 3: Context Assembly ───────────────────────────────────
    yield {"type": "stage", "stage": "Assembling context"}

    chat_history = session.chat_history[:-1] if session else []  # Exclude current message

    assembled_prompt = build_assembled_prompt(
        category=category,
        user_prompt=user_prompt,
        metadata=metadata,
        chat_history=chat_history,
    )

    # ── Layer 4: Master VLM ─────────────────────────────────────────
    yield {"type": "stage", "stage": "Generating analysis"}

    try:
        response_text = await generate_response(
            assembled_prompt=assembled_prompt,
            image_path=image_path,
            enhanced_image_path=enhanced_image_path,
        )
    except Exception as e:
        response_text = f"I encountered an error generating the analysis: {str(e)}"
        yield {"type": "stage", "stage": "Analysis encountered an issue"}

    # Save assistant response to session
    if session:
        session.add_message("assistant", response_text)

    # Stream response tokens
    for i in range(0, len(response_text), 4):
        chunk = response_text[i:i + 4]
        yield {"type": "token", "content": chunk}
        await asyncio.sleep(0.01)

    # Final result event
    yield {
        "type": "result",
        "category": category,
        "metadata": metadata,
        "enhanced_image_path": enhanced_image_path,
    }


async def run_followup(
    session_id: str,
    user_message: str,
    image_path: str,
    metadata: dict,
    enhanced_image_path: str = None,
    category: str = "general",
    chat_history: list[dict] = None,
) -> str:
    """Run a follow-up query using cached metadata (no re-processing).

    Args:
        session_id: Active session identifier.
        user_message: The follow-up question.
        image_path: Path to the original image.
        metadata: Cached metadata from initial pipeline run.
        enhanced_image_path: Optional enhanced image path.
        category: Previously classified category.
        chat_history: Previous conversation messages.

    Returns:
        The VLM response text.
    """
    response_text = await generate_followup_response(
        user_message=user_message,
        image_path=image_path,
        metadata=metadata,
        enhanced_image_path=enhanced_image_path,
        category=category,
        chat_history=chat_history,
    )

    # Save to session
    session = session_manager.get_session(session_id)
    if session:
        session.add_message("assistant", response_text)

    return response_text
