# glyph_forge/core/workspace/workspace.py
"""
Workspace wrapper that re-exports the SDK's Workspace class.

This maintains backwards compatibility while using the SDK's implementation.
"""

from __future__ import annotations

from typing import Optional, Dict

# Import Workspace from SDK
from glyph.core.workspace import Workspace


def create_workspace(
    *,
    root_dir: Optional[str] = None,
    use_uuid: bool = False,
    custom_paths: Optional[Dict[str, str]] = None,
) -> Workspace:
    """
    Create a filesystem-backed workspace.

    Args:
        root_dir: Base directory for storing artifacts (default: auto-detected)
        use_uuid: Whether to create a unique run folder (timestamp+uuid)
        custom_paths: Optional overrides for default paths

    Returns:
        Workspace instance
    """
    return Workspace(
        root_dir=root_dir,
        use_uuid=use_uuid,
        custom_paths=custom_paths,
    )


# Deprecated - kept for backwards compatibility
WorkspaceFactory = None
EngineFactory = None
WorkspaceConfig = None


def create_engine(workspace: Workspace, config: Optional[any] = None) -> None:
    """Deprecated - no longer used."""
    raise NotImplementedError("create_engine is deprecated in SDK mode")


__all__ = [
    "Workspace",
    "create_workspace",
    "create_engine",
    "WorkspaceFactory",
    "EngineFactory",
    "WorkspaceConfig",
]
