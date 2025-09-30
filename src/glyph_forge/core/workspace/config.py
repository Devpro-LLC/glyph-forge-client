# settings.py
import os
from dataclasses import dataclass

@dataclass
class WorkspaceConfig:
    mode: str = os.getenv("GLYPH_MODE", "local")  # "local" | "client"
    api_base: str | None = os.getenv("GLYPH_API_BASE")
    api_key: str | None  = os.getenv("GLYPH_API_KEY")
    timeout: float = float(os.getenv("GLYPH_API_TIMEOUT", "30"))
