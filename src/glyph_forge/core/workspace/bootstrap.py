# factory.py
from glyph_forge.core.workspace.storage.base import WorkspaceBase
from glyph_forge.core.workspace.config import WorkspaceConfig
from glyph_forge.core.workspace.runtime.adapters.local import LocalEngineAdapter
from glyph_forge.core.workspace.runtime.adapters.client import ClientEngineAdapter
from glyph_forge.core.workspace.runtime.engine import GlyphEngine

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
            adapter = ClientEngineAdapter(workspace, base_url=cfg.api_base, api_key=cfg.api_key, timeout=cfg.timeout)
        else:
            adapter = LocalEngineAdapter(workspace)
        return GlyphEngine(adapter)
