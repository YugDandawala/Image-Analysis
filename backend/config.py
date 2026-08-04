"""
Centralized configuration management using pydantic-settings.
All settings are loaded from environment variables / .env file.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application-wide configuration."""

    # --- Google Gemini ---
    GEMINI_API_KEY: str = ""

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # --- Image Processing ---
    MAX_IMAGE_SIZE_MB: int = 20
    UPLOAD_DIR: str = "temp"
    CLAHE_CLIP_LIMIT: float = 3.0
    CLAHE_GRID_SIZE: int = 8

    # --- Quality & Clarity Enhancer ---
    BLUR_THRESHOLD: float = 120.0
    MIN_DIMENSION_THRESHOLD: int = 800
    AUTO_ENHANCE_QUALITY: bool = True

    # --- Session Management ---
    SESSION_TTL_MINUTES: int = 60

    # --- Gemini Model IDs ---
    TRIAGE_MODEL: str = "gemini-3.5-flash-lite"
    UI_GROUNDING_MODEL: str = "gemini-3.5-flash"
    MASTER_VLM_MODEL: str = "gemini-3.5-flash"

    # --- Vision & Feature Models ---
    HUGGINGFACE_API_KEY: str = ""
    SAM2_MODEL_ID: str = "facebook/sam2-hiera-large"
    DINOV2_MODEL_ID: str = "facebook/dinov2-base"

    # --- Advanced Pipeline Flags ---
    ENABLE_VISUAL_OVERLAY: bool = True
    ENABLE_FOCUS_ZOOM: bool = True
    ENABLE_CLAIM_VERIFICATION: bool = True

    # --- Computed Paths ---
    @property
    def project_root(self) -> Path:
        """Return the project root directory (parent of backend/)."""
        return Path(__file__).resolve().parent.parent

    @property
    def upload_path(self) -> Path:
        """Full path to the upload/temp directory."""
        return self.project_root / self.UPLOAD_DIR

    @property
    def max_image_bytes(self) -> int:
        """Maximum upload size in bytes."""
        return self.MAX_IMAGE_SIZE_MB * 1024 * 1024

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
