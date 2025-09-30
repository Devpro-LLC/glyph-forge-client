# glyph/core/workspace/adapters/client.py
from __future__ import annotations

import json
from typing import Dict, List, Optional

from glyph_forge.core.workspace.runtime.engine import EngineAdapter, EngineConfigError, EngineIOError, _json_bytes
from glyph_forge.core.workspace.storage.base import WorkspaceBase

# httpx is recommended; replace with `requests` if you prefer.
try:
    import httpx
except Exception as exc:  # pragma: no cover
    httpx = None
    _import_err = exc
else:
    _import_err = None


class ClientEngineAdapter(EngineAdapter):
    """
    Calls FastAPI endpoints exposed by glyph-forge (or your hosted API).
    Expected endpoints (adjust paths if yours differ):
      - POST /schema/build          -> returns JSON schema
      - POST /schema/run            -> returns list of blocks/outputs
      - POST /plaintext/intake      -> returns structured plaintext analysis
    """

    def __init__(
        self,
        workspace: WorkspaceBase,
        *,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        if httpx is None:
            raise EngineConfigError(
                f"httpx is required for ClientEngineAdapter but failed to import: {_import_err}"
            )
        if not base_url:
            raise EngineConfigError("ClientEngineAdapter requires a non-empty base_url")

        self.ws = workspace
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=({"Authorization": f"Bearer {api_key}"} if api_key else {}),
            timeout=timeout,
        )

    # --------------- API calls ----------------

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
        try:
            with open(plaintext_path, "rb") as fp:
                resp = self._client.post(
                    "/plaintext/intake",
                    files={"plaintext": ("input.txt", fp, "text/plain")},
                    data={"options": json.dumps(options or {})},
                )
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            raise EngineIOError(f"Network error during intake_plaintext: {e}") from e
