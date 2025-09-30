# glyph/core/workspace/workspace.py
"""
Backwards-compatible workspace entrypoint.

- Keeps `Workspace` import stable for existing callers.
- Exposes factories (`WorkspaceFactory`, `EngineFactory`) and `WorkspaceConfig`.
- Adds tiny convenience helpers `create_workspace` and `create_engine`.

Usage (local SDK):
    from glyph_forge.core.workspace.workspace import Workspace, create_engine
    ws = Workspace(use_uuid=True)
    engine = create_engine(ws)  # local by default (GLYPH_MODE=local)

Usage (client / FastAPI):
    import os
    os.environ["GLYPH_MODE"] = "client"
    os.environ["GLYPH_API_BASE"] = "https://api.glyphapi.ai"
    os.environ["GLYPH_API_KEY"] = "<token>"

    from glyph_forge.core.workspace.workspace import Workspace, create_engine
    ws = Workspace(use_uuid=True)
    engine = create_engine(ws)  # client adapter auto-selected
"""

from __future__ import annotations

from typing import Optional, Dict

# Public surface for callers that previously did:
#   from glyph_forge.core.workspace.workspace import Workspace
from glyph_forge.core.workspace.storage.fs import FilesystemWorkspace as Workspace  # noqa: F401

# New configurable pieces
from glyph_forge.core.workspace.bootstrap import WorkspaceFactory, EngineFactory  # noqa: F401
from glyph_forge.core.workspace.config import WorkspaceConfig  # noqa: F401
from .runtime.engine import GlyphEngine  # type: ignore  # exposed for typing only


def create_workspace(
    *,
    root_dir: Optional[str] = None,
    use_uuid: bool = False,
    custom_paths: Optional[Dict[str, str]] = None,
) -> Workspace:
    """
    Convenience helper to create a filesystem-backed workspace using the
    new factory while keeping a stable import surface.

    Equivalent to: WorkspaceFactory.create(...)
    """
    return WorkspaceFactory.create(
        root_dir=root_dir,
        use_uuid=use_uuid,
        custom_paths=custom_paths,
    )


def create_engine(
    workspace: Workspace,
    config: Optional[WorkspaceConfig] = None,
) -> "GlyphEngine":
    """
    Convenience helper to build a mode-aware engine (local/client) for the
    provided workspace. Mode is selected via `config` or environment
    (see `WorkspaceConfig` for GLYPH_* variables).

    Equivalent to: EngineFactory.create(workspace, config)
    """
    return EngineFactory.create(workspace, cfg=config)


__all__ = [
    # Back-compat alias
    "Workspace",
    # New factories & config
    "WorkspaceFactory",
    "EngineFactory",
    "WorkspaceConfig",
    # Convenience creators
    "create_workspace",
    "create_engine",
]
