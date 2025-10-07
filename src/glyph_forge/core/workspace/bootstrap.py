# factory.py
from glyph_forge.core.workspace.storage.base import WorkspaceBase
from glyph_forge.core.workspace.config import WorkspaceConfig
from glyph_forge.core.workspace.runtime.adapters.client import ClientEngineAdapter
from glyph_forge.core.workspace.runtime.engine import GlyphEngine

# Import LocalEngineAdapter conditionally
try:
    from glyph_forge.core.workspace.runtime.adapters.local import LocalEngineAdapter, HAS_SDK
except ImportError:
    HAS_SDK = False
    LocalEngineAdapter = None

class WorkspaceFactory:
    @staticmethod
    def create(root_dir=None, use_uuid=False, custom_paths=None) -> WorkspaceBase:
        from glyph_forge.core.workspace.storage.fs import FilesystemWorkspace
        return FilesystemWorkspace(root_dir=root_dir, use_uuid=use_uuid, custom_paths=custom_paths)

class EngineFactory:
    @staticmethod
    def create(workspace: WorkspaceBase, cfg: WorkspaceConfig | None = None) -> GlyphEngine:
        cfg = cfg or WorkspaceConfig()

        if cfg.mode == "client":
            # Always use client adapter when explicitly requested
            adapter = ClientEngineAdapter(workspace, base_url=cfg.api_base, api_key=cfg.api_key, timeout=cfg.timeout)
        elif cfg.mode == "local":
            # User explicitly requested local mode
            if not HAS_SDK:
                raise ImportError(
                    "Local mode requires the glyph-sdk package to be installed. "
                    "Either install glyph-sdk for local development, or use client mode: "
                    "set GLYPH_MODE='client' or pass WorkspaceConfig(mode='client')"
                )
            adapter = LocalEngineAdapter(workspace)
        else:
            # Auto mode: prefer client if SDK not available, local if it is
            if HAS_SDK:
                adapter = LocalEngineAdapter(workspace)
            else:
                # Default to client mode when SDK isn't available
                adapter = ClientEngineAdapter(workspace, base_url=cfg.api_base, api_key=cfg.api_key, timeout=cfg.timeout)

        return GlyphEngine(adapter)
