"""
Report Exporter API.

Generates structured downloadable analysis reports (Markdown format) for a given session.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from backend.services.session_manager import session_manager

router = APIRouter()


@router.get("/report/{session_id}")
async def export_session_report(session_id: str):
    """Export session analysis summary report as Markdown.

    Args:
        session_id: Session identifier.

    Returns:
        Markdown text file download response.
    """
    session = session_manager.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    lines = []
    lines.append(f"# Universal Image Analysis Report")
    lines.append(f"**Session ID:** `{session.session_id}`  ")
    lines.append(f"**Original Filename:** `{session.original_filename}`  ")
    lines.append(f"**Classified Category:** `{session.category or 'General'}`  ")
    lines.append(f"\n---\n")

    # Image Quality & Preprocessing
    if session.quality_info:
        lines.append("## 1. Image Quality & Preprocessing")
        lines.append(f"- **Laplacian Variance Blur Metric:** `{session.quality_info.get('laplacian_var')}`")
        lines.append(f"- **Original Dimensions:** `{session.quality_info.get('dimensions')}`")
        lines.append(f"- **Resolution Restored:** `{bool(session.restored_image_path)}`\n")

    # Extracted Ground Truth
    if session.metadata:
        lines.append("## 2. Extracted Structural Metadata")
        if "description" in session.metadata:
            lines.append(f"**Summary:** {session.metadata['description']}\n")

        if "tables" in session.metadata and session.metadata["tables"]:
            lines.append("### Extracted Tables")
            for i, tbl in enumerate(session.metadata["tables"], 1):
                lines.append(f"#### Table {i}")
                lines.append(tbl.get("markdown", str(tbl)))
                lines.append("")

        if "elements" in session.metadata and session.metadata["elements"]:
            lines.append(f"### Detected UI Elements ({len(session.metadata['elements'])} found)")
            for elem in session.metadata["elements"][:10]:
                lines.append(f"- **{elem.get('label')}** (`{elem.get('element_type')}`) — Box: `{elem.get('box_2d')}`")
            lines.append("")

    # Chat Conversation & Analysis
    if session.chat_history:
        lines.append("## 3. Conversational Analysis & Findings")
        for msg in session.chat_history:
            role = "User Query" if msg["role"] == "user" else "AI Analysis"
            lines.append(f"### {role}")
            lines.append(msg["content"])
            lines.append("")

    report_content = "\n".join(lines)

    return Response(
        content=report_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=Analysis_Report_{session_id}.md"
        },
    )
