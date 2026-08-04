"""
Chat and conversation endpoints.
Handles both initial analysis (triggers full pipeline) and follow-up questions.
Uses SSE (Server-Sent Events) for streaming responses.
"""

import json
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from backend.models.schemas import ChatRequest, PipelineStatusResponse
from backend.services.session_manager import session_manager
from backend.pipeline.graph import run_pipeline, run_followup

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """Send a message in an analysis session.

    If this is the first message (or no cached metadata exists),
    the full pipeline runs: Triage → Specialist Module → Context Assembly → VLM.

    If cached metadata exists (follow-up question), only the Master VLM is invoked.

    Returns a streaming SSE response.
    """
    session = session_manager.get_session(request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please upload a new image.")

    # Add user message to history
    session.add_message("user", request.message)

    async def event_stream():
        """Generator that yields SSE events."""
        try:
            if session.has_cached_metadata:
                # Follow-up: skip pipeline, go directly to Master VLM
                yield f"data: {json.dumps({'type': 'stage', 'stage': 'Generating response'})}\n\n"

                response_text = await run_followup(
                    session_id=request.session_id,
                    user_message=request.message,
                    image_path=session.image_path,
                    metadata=session.metadata,
                    enhanced_image_path=session.enhanced_image_path,
                    category=session.category,
                    chat_history=session.chat_history[:-1],  # Exclude the message we just added
                )

                # Stream response character-by-character for smooth UX
                for i in range(0, len(response_text), 4):
                    chunk = response_text[i:i + 4]
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.01)

            else:
                # First message: run full pipeline with stage updates
                async for event in run_pipeline(
                    session_id=request.session_id,
                    user_prompt=request.message,
                    image_path=session.image_path,
                ):
                    yield f"data: {json.dumps(event)}\n\n"

                    # Update session with pipeline results
                    if event.get("type") == "stage":
                        session.update_stage(event["stage"])
                    elif event.get("type") == "result":
                        session.category = event.get("category", session.category)
                        session.metadata = event.get("metadata", session.metadata)
                        session.enhanced_image_path = event.get("enhanced_image_path", session.enhanced_image_path)
                        session.restored_image_path = event.get("restored_image_path", session.restored_image_path)
                        session.quality_info = event.get("quality_info", session.quality_info)
                        session.annotated_image_path = event.get("annotated_image_path", session.annotated_image_path)
                        session.annotated_url = event.get("annotated_url", session.annotated_url)
                        session.focus_crop_path = event.get("focus_crop_path", session.focus_crop_path)
                        session.verification_report = event.get("verification_report", session.verification_report)
                        session.mark_complete()

            # Final: send done event and save assistant message
            full_response = session.chat_history[-1]["content"] if session.chat_history and session.chat_history[-1]["role"] == "assistant" else ""
            yield f"data: {json.dumps({'type': 'done', 'category': session.category})}\n\n"

        except Exception as e:
            session.error = str(e)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/{session_id}/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(session_id: str):
    """Get the current pipeline processing status for a session."""
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    return PipelineStatusResponse(
        session_id=session_id,
        current_stage=session.processing_stage,
        completed_stages=session.completed_stages,
        is_complete=session.is_pipeline_complete,
        category=session.category,
        error=session.error,
    )
