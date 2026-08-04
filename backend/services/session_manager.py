"""
In-memory session manager for tracking pipeline state and chat history.
Sessions are cached so follow-up questions skip the preprocessing pipeline.
"""

import time
from typing import Optional, Any
from backend.config import get_settings


class Session:
    """Represents a single user analysis session."""

    def __init__(self, session_id: str, image_path: str, original_filename: str):
        self.session_id = session_id
        self.image_path = image_path
        self.original_filename = original_filename
        self.created_at = time.time()
        self.last_accessed = time.time()

        # Pipeline results (cached after first run)
        self.category: Optional[str] = None
        self.metadata: dict[str, Any] = {}
        self.enhanced_image_path: Optional[str] = None
        self.quality_info: Optional[dict[str, Any]] = None
        self.restored_image_path: Optional[str] = None
        self.assembled_context: Optional[str] = None

        # Conversation history
        self.chat_history: list[dict[str, str]] = []

        # Pipeline tracking
        self.processing_stage: str = "idle"
        self.completed_stages: list[str] = []
        self.is_pipeline_complete: bool = False
        self.error: Optional[str] = None

    def touch(self):
        """Update last accessed timestamp."""
        self.last_accessed = time.time()

    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        self.chat_history.append({"role": role, "content": content})
        self.touch()

    def update_stage(self, stage: str):
        """Update the current processing stage."""
        if self.processing_stage != "idle" and self.processing_stage not in self.completed_stages:
            self.completed_stages.append(self.processing_stage)
        self.processing_stage = stage
        self.touch()

    def mark_complete(self):
        """Mark the pipeline as complete."""
        if self.processing_stage not in self.completed_stages:
            self.completed_stages.append(self.processing_stage)
        self.processing_stage = "complete"
        self.is_pipeline_complete = True
        self.touch()

    @property
    def has_cached_metadata(self) -> bool:
        """Check if this session already has processed metadata (for follow-ups)."""
        return self.is_pipeline_complete and bool(self.metadata)

    @property
    def is_expired(self) -> bool:
        """Check if this session has exceeded its TTL."""
        settings = get_settings()
        ttl_seconds = settings.SESSION_TTL_MINUTES * 60
        return (time.time() - self.last_accessed) > ttl_seconds


class SessionManager:
    """Manages all active analysis sessions in memory."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self, session_id: str, image_path: str, original_filename: str) -> Session:
        """Create and register a new session."""
        session = Session(session_id, image_path, original_filename)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve a session by ID, returning None if not found or expired."""
        session = self._sessions.get(session_id)
        if session is None:
            return None
        if session.is_expired:
            self.remove_session(session_id)
            return None
        session.touch()
        return session

    def remove_session(self, session_id: str):
        """Remove a session from the manager."""
        self._sessions.pop(session_id, None)

    def cleanup_expired(self):
        """Remove all expired sessions."""
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if session.is_expired
        ]
        for sid in expired_ids:
            self.remove_session(sid)

    @property
    def active_count(self) -> int:
        """Number of active sessions."""
        return len(self._sessions)


# Global singleton instance
session_manager = SessionManager()
