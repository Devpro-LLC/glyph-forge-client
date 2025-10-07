# glyph/core/workspace/adapters/local.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from glyph_forge.core.workspace.runtime.engine import EngineAdapter, EngineIOError, _json_bytes
from glyph_forge.core.workspace.storage.base import WorkspaceBase
import httpx

# Optional SDK imports - only available in development environment
try:
    from glyph.core.schema_runner.run_schema import GlyphSchemaRunner
    from glyph.core.analysis.plaintext.intake import intake_plaintext
    from glyph.core.schema.build_schema import GlyphSchemaBuilder
    HAS_SDK = True
except ImportError:
    HAS_SDK = False


class LocalEngineAdapter(EngineAdapter):
    """
    Executes everything locally using the SDK's existing modules.

    Note: Requires the glyph-sdk package to be installed. This adapter
    is only available in development environments with SDK access.
    """

    def __init__(self, workspace: WorkspaceBase):
        if not HAS_SDK:
            raise ImportError(
                "LocalEngineAdapter requires the glyph-sdk package. "
                "Install it for local development, or use the API client mode instead. "
                "Set GLYPH_MODE='client' to use the remote API."
            )
        self.ws = workspace

    def build_schema(
        self,
        *,
        docx_path: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> Dict:
        files = {}
        try:
            if docx_path:
                files["docx"] = ("input.docx", open(docx_path, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if plaintext_path:
                files["plaintext"] = ("input.txt", open(plaintext_path, "rb"), "text/plain")

            # NOTE: Some servers expect multipart for files + data.
            # If your server expects JSON, change to json=... and move files accordingly.
            resp = self._client.post(
                "/schema/build",
                files=files if files else None,
                data={"options": json.dumps(options or {})} if files else None,
                json=( {"options": options or {}} if not files else None ),
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise EngineIOError(f"Network error during build_schema: {e}") from e
        finally:
            for f in files.values():
                # f is a tuple(file_name, file_obj, mime)
                if hasattr(f[1], "close"):
                    f[1].close()

    def run_schema(
        self,
        *,
        schema: Dict,
        source_docx: Optional[str],
        plaintext_path: Optional[str],
        options: Dict
    ) -> List:
        files = {
            "schema": ("schema.json", _json_bytes(schema), "application/json"),
        }
        try:
            if source_docx:
                files["docx"] = ("input.docx", open(source_docx, "rb"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            if plaintext_path:
                files["plaintext"] = ("input.txt", open(plaintext_path, "rb"), "text/plain")

            resp = self._client.post(
                "/schema/run",
                files=files,
                data={"options": json.dumps(options or {})},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise EngineIOError(f"Network error during run_schema: {e}") from e
        finally:
            for k, f in list(files.items()):
                if k == "schema":
                    continue
                if hasattr(f[1], "close"):
                    f[1].close()


    def intake_plaintext(
        self,
        *,
        plaintext_path: str,
        options: Dict
    ) -> Dict:
        # Existing plaintext intake utility
        return intake_plaintext(plaintext_path, **(options or {}))
