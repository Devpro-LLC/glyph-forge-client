# glyph_forge/core/client/forge_client.py
"""
ForgeClient: Synchronous HTTP client for Glyph Forge API.

MVP features:
- No authentication (no API keys)
- Synchronous HTTP only
- Integration with workspace for local artifact persistence
- Basic logging (INFO for operations, DEBUG for request/response details)
"""

from __future__ import annotations

import logging
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

import httpx

from .exceptions import ForgeClientError, ForgeClientIOError, ForgeClientHTTPError


logger = logging.getLogger(__name__)


class ForgeClient:
    """
    Synchronous HTTP client for Glyph Forge API.

    Args:
        base_url: Base URL for the API. If not provided, falls back to:
                  1) GLYPH_API_BASE environment variable
                  2) Default: "https://api.glyphapi.ai"
        timeout: Request timeout in seconds (default: 30.0)

    Example:
        >>> # Uses default or GLYPH_API_BASE
        >>> client = ForgeClient()
        >>>
        >>> # Or specify explicitly
        >>> client = ForgeClient("https://api.glyphapi.ai")
        >>> schema = client.build_schema_from_docx(ws, docx_path="sample.docx")
    """

    DEFAULT_BASE_URL = "https://api.glyphapi.ai"

    def __init__(self, base_url: Optional[str] = None, *, timeout: float = 30.0):
        """
        Initialize ForgeClient.

        Args:
            base_url: Base URL for API (no trailing slash). Falls back to
                      GLYPH_API_BASE env var or default URL if not provided.
            timeout: Default timeout for all requests in seconds
        """
        resolved_url = base_url or os.getenv("GLYPH_API_BASE") or self.DEFAULT_BASE_URL
        self.base_url = resolved_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)
        logger.info(f"ForgeClient initialized with base_url={self.base_url}, timeout={timeout}s")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Internal helper to make HTTP requests with error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path (e.g., "/schema/build")
            json_data: JSON payload for request body
            files: Multipart files for upload
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: Non-2xx HTTP responses
        """
        url = f"{self.base_url}{endpoint}"
        payload_summary = None

        if json_data:
            # Create summary for logging/errors (truncate large payloads)
            payload_str = json.dumps(json_data)
            if len(payload_str) > 100:
                payload_summary = payload_str[:100] + "..."
            else:
                payload_summary = payload_str

        logger.info(f"{method} {endpoint}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Request: {method} {url}")
            if json_data:
                logger.debug(f"Payload: {json_data}")
            if params:
                logger.debug(f"Params: {params}")

        try:
            response = self._client.request(
                method=method,
                url=url,
                json=json_data,
                files=files,
                params=params,
            )

            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Response status: {response.status_code}, size: {len(response.content)} bytes")

            # Check for non-2xx status
            if not (200 <= response.status_code < 300):
                body = response.text
                raise ForgeClientHTTPError(
                    f"HTTP {response.status_code} from {endpoint}",
                    status_code=response.status_code,
                    response_body=body,
                    endpoint=endpoint,
                )

            # Parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise ForgeClientError(
                    f"Invalid JSON response from {endpoint}",
                    endpoint=endpoint,
                ) from e

        except httpx.TimeoutException as e:
            raise ForgeClientIOError(
                f"Request timeout for {endpoint}",
                endpoint=endpoint,
                original_error=e,
            ) from e
        except httpx.NetworkError as e:
            raise ForgeClientIOError(
                f"Network error for {endpoint}",
                endpoint=endpoint,
                original_error=e,
            ) from e
        except httpx.HTTPError as e:
            # Catch any other httpx errors
            raise ForgeClientIOError(
                f"HTTP client error for {endpoint}",
                endpoint=endpoint,
                original_error=e,
            ) from e

    # -------------------------------------------------------------------------
    # Schema Build
    # -------------------------------------------------------------------------

    def build_schema_from_docx(
        self,
        ws: Any,  # Workspace type from glyph.core.workspace
        *,
        docx_path: str,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a schema from a DOCX file via the API.

        Endpoint: POST /schema/build

        Args:
            ws: Workspace instance for saving artifacts
            docx_path: Path to DOCX file (absolute or CWD-relative)
            save_as: Optional name to save schema JSON (without .json extension)

        Returns:
            Schema dict from API response

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status

        Example:
            >>> schema = client.build_schema_from_docx(
            ...     ws,
            ...     docx_path="sample.docx",
            ...     save_as="my_schema"
            ... )
        """
        logger.info(f"Building schema from docx_path={docx_path}, save_as={save_as}")

        # Resolve path to absolute
        docx_abs = str(Path(docx_path).resolve())

        response = self._make_request(
            "POST",
            "/schema/build",
            json_data={"docx_path": docx_abs},
        )

        schema = response.get("schema")
        if not schema:
            raise ForgeClientError(
                "Missing 'schema' in API response",
                endpoint="/schema/build",
            )

        # Save to workspace if requested
        if save_as:
            try:
                schema_path = ws.save_json("output_configs", save_as, schema)
                logger.info(f"Schema saved to {schema_path}")
            except Exception as e:
                raise ForgeClientError(
                    f"Failed to save schema to workspace: {e}",
                    endpoint="/schema/build",
                ) from e

        return schema

    # -------------------------------------------------------------------------
    # Schema Run
    # -------------------------------------------------------------------------

    def run_schema(
        self,
        ws: Any,  # Workspace type
        *,
        schema: Dict[str, Any],
        plaintext: str,
        dest_name: str = "assembled_output.docx",
    ) -> str:
        """
        Run a schema with plaintext to generate a DOCX.

        Endpoint: POST /schema/run

        Args:
            ws: Workspace instance
            schema: Schema dict (from build_schema_from_docx or loaded JSON)
            plaintext: Input text content
            dest_name: Name for output DOCX (used in manifest)

        Returns:
            Server-side docx_url (or local path if download is implemented)

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status

        Note:
            In MVP, the server returns a server-side path. This method saves
            metadata to workspace (run_manifest.json). Future versions may
            download the DOCX to ws.directory("output_docx").

        Example:
            >>> docx_url = client.run_schema(
            ...     ws,
            ...     schema=schema,
            ...     plaintext="Sample text...",
            ...     dest_name="output.docx"
            ... )
        """
        logger.info(f"Running schema with plaintext length={len(plaintext)}, dest_name={dest_name}")

        response = self._make_request(
            "POST",
            "/schema/run",
            json_data={"schema": schema, "plaintext": plaintext},
        )

        status = response.get("status")
        docx_url = response.get("docx_url")

        if status != "success":
            raise ForgeClientError(
                f"Schema run failed with status={status}",
                endpoint="/schema/run",
            )

        if not docx_url:
            raise ForgeClientError(
                "Missing 'docx_url' in API response",
                endpoint="/schema/run",
            )

        # Save run manifest to workspace
        try:
            # Compute schema hash for reference
            schema_str = json.dumps(schema, sort_keys=True)
            schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]

            manifest = {
                "timestamp": datetime.now().isoformat(),
                "schema_hash": schema_hash,
                "docx_url": docx_url,
                "dest_name": dest_name,
                "plaintext_length": len(plaintext),
                "status": status,
            }

            manifest_path = ws.save_json("output_configs", "run_manifest", manifest)
            logger.info(f"Run manifest saved to {manifest_path}")
        except Exception as e:
            # Don't fail the call, but log the error
            logger.warning(f"Failed to save run manifest: {e}")

        logger.info(f"Schema run completed, docx_url={docx_url}")
        return docx_url

    # -------------------------------------------------------------------------
    # Plaintext Intake (JSON body)
    # -------------------------------------------------------------------------

    def intake_plaintext_text(
        self,
        ws: Any,  # Workspace type
        *,
        text: str,
        save_as: Optional[str] = None,
        **opts: Any,
    ) -> Dict[str, Any]:
        """
        Intake plaintext via JSON body.

        Endpoint: POST /plaintext/intake

        Args:
            ws: Workspace instance
            text: Plaintext content to intake
            save_as: Optional name to save intake result JSON
            **opts: Additional options matching PlaintextIntakeRequest fields:
                - unicode_form: str (default: "NFC")
                - strip_zero_width: bool (default: True)
                - expand_tabs: bool (default: True)
                - ensure_final_newline: bool (default: True)
                - max_bytes: int (default: 10MB)
                - filename: str (optional)

        Returns:
            Intake result dict from API

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status

        Example:
            >>> result = client.intake_plaintext_text(
            ...     ws,
            ...     text="Sample text...",
            ...     save_as="intake_result",
            ...     strip_zero_width=False
            ... )
        """
        logger.info(f"Intaking plaintext (text length={len(text)}), save_as={save_as}")

        payload = {"text": text, **opts}

        response = self._make_request(
            "POST",
            "/plaintext/intake",
            json_data=payload,
        )

        # Save to workspace if requested
        if save_as:
            try:
                result_path = ws.save_json("output_configs", save_as, response)
                logger.info(f"Intake result saved to {result_path}")
            except Exception as e:
                raise ForgeClientError(
                    f"Failed to save intake result to workspace: {e}",
                    endpoint="/plaintext/intake",
                ) from e

        return response

    # -------------------------------------------------------------------------
    # Plaintext Intake (file upload)
    # -------------------------------------------------------------------------

    def intake_plaintext_file(
        self,
        ws: Any,  # Workspace type
        *,
        file_path: str,
        save_as: Optional[str] = None,
        **opts: Any,
    ) -> Dict[str, Any]:
        """
        Intake plaintext via file upload.

        Endpoint: POST /plaintext/intake_file

        Args:
            ws: Workspace instance
            file_path: Path to plaintext file
            save_as: Optional name to save intake result JSON
            **opts: Query parameters for normalization options:
                - unicode_form: str
                - strip_zero_width: bool
                - expand_tabs: bool
                - ensure_final_newline: bool

        Returns:
            Intake result dict from API

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status
            ForgeClientError: File not found or unreadable

        Example:
            >>> result = client.intake_plaintext_file(
            ...     ws,
            ...     file_path="sample.txt",
            ...     save_as="intake_result",
            ...     unicode_form="NFKC"
            ... )
        """
        logger.info(f"Intaking plaintext from file_path={file_path}, save_as={save_as}")

        # Resolve and validate file path
        file_abs = Path(file_path).resolve()
        if not file_abs.exists():
            raise ForgeClientError(
                f"File not found: {file_abs}",
                endpoint="/plaintext/intake_file",
            )
        if not file_abs.is_file():
            raise ForgeClientError(
                f"Not a file: {file_abs}",
                endpoint="/plaintext/intake_file",
            )

        # Open file and prepare multipart
        try:
            with open(file_abs, "rb") as f:
                files = {"file": (file_abs.name, f, "text/plain")}
                response = self._make_request(
                    "POST",
                    "/plaintext/intake_file",
                    files=files,
                    params=opts if opts else None,
                )
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read file {file_abs}: {e}",
                endpoint="/plaintext/intake_file",
            ) from e

        # Save to workspace if requested
        if save_as:
            try:
                result_path = ws.save_json("output_configs", save_as, response)
                logger.info(f"Intake result saved to {result_path}")
            except Exception as e:
                raise ForgeClientError(
                    f"Failed to save intake result to workspace: {e}",
                    endpoint="/plaintext/intake_file",
                ) from e

        return response

    def __repr__(self) -> str:
        return f"ForgeClient(base_url={self.base_url!r}, timeout={self.timeout})"