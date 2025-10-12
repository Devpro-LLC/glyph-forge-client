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
        api_key: API key for authentication (required). Format: "gf_live_..." or "gf_test_...".
                 Can also be read from GLYPH_API_KEY environment variable.
        base_url: Base URL for the API. If not provided, falls back to:
                  1) GLYPH_API_BASE environment variable
                  2) Default: "https://dev.glyphapi.ai"
        timeout: Request timeout in seconds (default: 30.0)

    Example:
        >>> # Uses GLYPH_API_KEY env var and default base URL
        >>> client = ForgeClient()
        >>>
        >>> # Or specify explicitly
        >>> client = ForgeClient(api_key="gf_live_abc123...", base_url="https://api.glyphapi.ai")
        >>> schema = client.build_schema_from_docx(ws, docx_path="sample.docx")
    """

    DEFAULT_BASE_URL = "https://dev.glyphapi.ai"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        *,
        timeout: float = 30.0
    ):
        """
        Initialize ForgeClient.

        Args:
            api_key: API key for authentication. Falls back to GLYPH_API_KEY env var if not provided.
            base_url: Base URL for API (no trailing slash). Falls back to
                      GLYPH_API_BASE env var or default URL if not provided.
            timeout: Default timeout for all requests in seconds

        Raises:
            ForgeClientError: If no API key is provided or found in environment
        """
        # Resolve API key
        self.api_key = api_key or os.getenv("GLYPH_API_KEY")
        if not self.api_key:
            raise ForgeClientError(
                "API key is required. Provide via api_key parameter or GLYPH_API_KEY environment variable."
            )

        # Resolve base URL
        resolved_url = base_url or os.getenv("GLYPH_API_BASE") or self.DEFAULT_BASE_URL
        self.base_url = resolved_url.rstrip("/")
        self.timeout = timeout

        # Initialize HTTP client with default headers
        headers = {"Authorization": f"Bearer {self.api_key}"}
        self._client = httpx.Client(timeout=timeout, headers=headers)

        # Rate limit tracking
        self.last_rate_limit_info: Optional[Dict[str, str]] = None

        logger.info(f"ForgeClient initialized with base_url={self.base_url}, timeout={timeout}s")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.close()
        return False

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
            endpoint: API endpoint path (e.g., "/build")
            json_data: JSON payload for request body
            files: Multipart files for upload
            params: Query parameters

        Returns:
            Response JSON as dict

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: Non-2xx HTTP responses (401, 403, 429, etc.)
        """
        url = f"{self.base_url}{endpoint}"

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

            # Extract and store rate limit info from response headers
            rate_limit_headers = {
                "X-Subscription-Tier": response.headers.get("X-Subscription-Tier"),
                "X-Requests-Remaining": response.headers.get("X-Requests-Remaining"),
                "X-Rate-Limit": response.headers.get("X-Rate-Limit"),
            }
            # Only store if at least one header is present
            if any(rate_limit_headers.values()):
                self.last_rate_limit_info = rate_limit_headers
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Rate limit info: {rate_limit_headers}")

            # Check for non-2xx status
            if not (200 <= response.status_code < 300):
                body = response.text
                error_msg = f"HTTP {response.status_code} from {endpoint}"

                # Add context for common auth/rate limit errors
                if response.status_code == 401:
                    error_msg += " (Unauthorized - check API key)"
                elif response.status_code == 403:
                    error_msg += " (Forbidden - account inactive or no subscription)"
                elif response.status_code == 429:
                    error_msg += " (Rate limit exceeded)"

                raise ForgeClientHTTPError(
                    error_msg,
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

    def _save_artifacts_to_workspace(
        self,
        ws: Any,
        response: Dict[str, Any],
        original_docx_path: Path,
    ) -> None:
        """
        Save artifacts (tagged DOCX and unzipped files) to workspace.

        Args:
            ws: Workspace instance
            response: API response containing artifacts
            original_docx_path: Path to original input DOCX (for naming)

        Raises:
            Logs warnings on failure but does not raise exceptions
        """
        import base64

        tagged_docx_b64 = response.get("tagged_docx_base64")
        unzipped_files = response.get("unzipped_files", {})
        metadata = response.get("artifact_metadata", {})

        # Save tagged DOCX
        if tagged_docx_b64:
            try:
                tagged_bytes = base64.b64decode(tagged_docx_b64)
                run_id = metadata.get("run_id", "unknown")

                input_docx_dir = ws.directory("input_docx")
                # Use original filename with tag appended
                tagged_filename = f"{original_docx_path.stem}_{run_id}{original_docx_path.suffix}"
                tagged_path = Path(input_docx_dir) / tagged_filename

                with open(tagged_path, "wb") as f:
                    f.write(tagged_bytes)

                logger.info(f"Tagged DOCX saved to {tagged_path}")
            except Exception as e:
                logger.warning(f"Failed to save tagged DOCX: {e}")

        # Save unzipped XML files
        if unzipped_files:
            try:
                unzipped_dir = ws.directory("input_unzipped")
                run_id = metadata.get("run_id", "unknown")

                # Create subdirectory for this run to maintain structure
                run_unzipped_dir = Path(unzipped_dir) / f"{original_docx_path.stem}_{run_id}"

                for rel_path, content_b64 in unzipped_files.items():
                    file_bytes = base64.b64decode(content_b64)
                    full_path = run_unzipped_dir / rel_path

                    # Create parent directories
                    full_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(full_path, "wb") as f:
                        f.write(file_bytes)

                logger.info(f"Unzipped {len(unzipped_files)} files to {run_unzipped_dir}")
            except Exception as e:
                logger.warning(f"Failed to save unzipped files: {e}")

        # Save artifact metadata
        if metadata:
            try:
                ws.save_json("output_configs", "artifact_metadata", metadata)
                logger.info("Artifact metadata saved")
            except Exception as e:
                logger.warning(f"Failed to save artifact metadata: {e}")

    def build_schema_from_docx(
        self,
        ws: Any,  # Workspace type from glyph.core.workspace
        *,
        docx_path: str,
        save_as: Optional[str] = None,
        include_artifacts: bool = False,
    ) -> Dict[str, Any]:
        """
        Build a schema from a DOCX file via the API.

        Endpoint: POST /schema/build

        Args:
            ws: Workspace instance for saving artifacts
            docx_path: Path to DOCX file (absolute or CWD-relative)
            save_as: Optional name to save schema JSON (without .json extension)
            include_artifacts: If True, retrieve and save tagged DOCX + unzipped files
                              Adds ~300-800ms overhead depending on document complexity

        Returns:
            Schema dict from API response

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status (401, 403, 429)
            ForgeClientError: File not found or encoding error

        Example:
            >>> # Fast mode (schema only)
            >>> schema = client.build_schema_from_docx(
            ...     ws,
            ...     docx_path="sample.docx",
            ...     save_as="my_schema"
            ... )
            >>>
            >>> # Full mode (with artifacts for debugging/post-processing)
            >>> schema = client.build_schema_from_docx(
            ...     ws,
            ...     docx_path="sample.docx",
            ...     save_as="my_schema",
            ...     include_artifacts=True
            ... )
        """
        import base64

        logger.info(f"Building schema from docx_path={docx_path}, save_as={save_as}, include_artifacts={include_artifacts}")

        # Resolve path to absolute
        docx_abs = Path(docx_path).resolve()

        # Check if file exists
        if not docx_abs.exists():
            raise ForgeClientError(
                f"DOCX file not found: {docx_abs}",
                endpoint="/schema/build",
            )

        if not docx_abs.is_file():
            raise ForgeClientError(
                f"Not a file: {docx_abs}",
                endpoint="/schema/build",
            )

        # Read and encode DOCX file as base64
        try:
            with open(docx_abs, "rb") as f:
                docx_bytes = f.read()
            docx_base64 = base64.b64encode(docx_bytes).decode('utf-8')
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read DOCX file {docx_abs}: {e}",
                endpoint="/schema/build",
            ) from e

        response = self._make_request(
            "POST",
            "/schema/build",
            json_data={
                "docx_base64": docx_base64,
                "include_artifacts": include_artifacts
            },
        )

        schema = response.get("schema")
        if not schema:
            raise ForgeClientError(
                "Missing 'schema' in API response",
                endpoint="/schema/build",
            )

        # Save schema to workspace if requested
        if save_as:
            try:
                schema_path = ws.save_json("output_configs", save_as, schema)
                logger.info(f"Schema saved to {schema_path}")
            except Exception as e:
                raise ForgeClientError(
                    f"Failed to save schema to workspace: {e}",
                    endpoint="/schema/build",
                ) from e

        # Handle artifacts if included
        if include_artifacts:
            self._save_artifacts_to_workspace(ws, response, docx_abs)

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
            dest_name: Name for output DOCX file (saved in output_docx directory)

        Returns:
            Local path to saved DOCX file

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status
            ForgeClientError: Failed to decode or save DOCX

        Example:
            >>> docx_path = client.run_schema(
            ...     ws,
            ...     schema=schema,
            ...     plaintext="Sample text...",
            ...     dest_name="output.docx"
            ... )
        """
        import base64

        logger.info(f"Running schema with plaintext length={len(plaintext)}, dest_name={dest_name}")

        response = self._make_request(
            "POST",
            "/schema/run",
            json_data={"schema": schema, "plaintext": plaintext},
        )

        status = response.get("status")
        docx_base64 = response.get("docx_base64")

        if status != "success":
            raise ForgeClientError(
                f"Schema run failed with status={status}",
                endpoint="/schema/run",
            )

        if not docx_base64:
            raise ForgeClientError(
                "Missing 'docx_base64' in API response",
                endpoint="/schema/run",
            )

        # Decode base64 DOCX
        try:
            docx_bytes = base64.b64decode(docx_base64)
        except Exception as e:
            raise ForgeClientError(
                f"Failed to decode base64 DOCX: {e}",
                endpoint="/schema/run",
            ) from e

        # Save DOCX to workspace
        try:
            output_dir = ws.directory("output_docx")
            docx_path = Path(output_dir) / dest_name
            with open(docx_path, "wb") as f:
                f.write(docx_bytes)
            logger.info(f"DOCX saved to {docx_path}")
        except Exception as e:
            raise ForgeClientError(
                f"Failed to save DOCX to workspace: {e}",
                endpoint="/schema/run",
            ) from e

        # Save run manifest to workspace
        try:
            # Compute schema hash for reference
            schema_str = json.dumps(schema, sort_keys=True)
            schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]

            manifest = {
                "timestamp": datetime.now().isoformat(),
                "schema_hash": schema_hash,
                "docx_path": str(docx_path),
                "dest_name": dest_name,
                "plaintext_length": len(plaintext),
                "status": status,
            }

            manifest_path = ws.save_json("output_configs", "run_manifest", manifest)
            logger.info(f"Run manifest saved to {manifest_path}")
        except Exception as e:
            # Don't fail the call, but log the error
            logger.warning(f"Failed to save run manifest: {e}")

        logger.info(f"Schema run completed, docx saved to {docx_path}")
        return str(docx_path)

    def run_schema_bulk(
        self,
        ws: Any,  # Workspace type
        *,
        schema: Dict[str, Any],
        plaintexts: list[str],
        max_concurrent: int = 5,
        dest_name_pattern: str = "output_{index}.docx",
    ) -> Dict[str, Any]:
        """
        Run a schema with multiple plaintexts in parallel to generate multiple DOCX files.

        Endpoint: POST /schema/run/bulk

        Args:
            ws: Workspace instance
            schema: Schema dict (from build_schema_from_docx or loaded JSON)
            plaintexts: List of plaintext strings to process (max 100)
            max_concurrent: Number of concurrent processes (default: 5, max: 20)
            dest_name_pattern: Pattern for output filenames. Use {index} placeholder (default: "output_{index}.docx")

        Returns:
            Dict containing:
                - results: List of dicts with index, status, docx_path (or error)
                - total: Total number of plaintexts
                - successful: Number of successful runs
                - failed: Number of failed runs
                - processing_time_seconds: Total processing time
                - metered_count: Number of API calls metered

        Raises:
            ForgeClientError: If plaintexts exceeds 100 items or invalid parameters
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status (401, 403, 429)

        Note:
            Each plaintext counts as 1 API call for billing purposes.
            Failed items return error messages but don't block successful ones.
            All DOCX files are saved to workspace output_docx directory.

        Example:
            >>> result = client.run_schema_bulk(
            ...     ws,
            ...     schema=schema,
            ...     plaintexts=["Text 1...", "Text 2...", "Text 3..."],
            ...     max_concurrent=5,
            ...     dest_name_pattern="invoice_{index}.docx"
            ... )
            >>> print(f"Processed {result['successful']} of {result['total']}")
        """
        import base64

        if len(plaintexts) > 100:
            raise ForgeClientError(
                f"Too many plaintexts: {len(plaintexts)} (max 100 per request)",
                endpoint="/schema/run/bulk",
            )

        if len(plaintexts) == 0:
            raise ForgeClientError(
                "At least 1 plaintext is required",
                endpoint="/schema/run/bulk",
            )

        if not (1 <= max_concurrent <= 20):
            raise ForgeClientError(
                f"max_concurrent must be between 1 and 20, got {max_concurrent}",
                endpoint="/schema/run/bulk",
            )

        logger.info(
            f"Running schema in bulk with {len(plaintexts)} plaintexts, "
            f"max_concurrent={max_concurrent}"
        )

        response = self._make_request(
            "POST",
            "/schema/run/bulk",
            json_data={
                "schema": schema,
                "plaintexts": plaintexts,
                "max_concurrent": max_concurrent,
            },
        )

        # Process results and save DOCX files
        results = response.get("results", [])
        processed_results = []

        output_dir = ws.directory("output_docx")

        for result in results:
            index = result.get("index")
            status = result.get("status")
            docx_base64 = result.get("docx_base64")
            error = result.get("error")

            processed_result = {
                "index": index,
                "status": status,
            }

            if status == "success" and docx_base64:
                try:
                    # Decode and save DOCX
                    docx_bytes = base64.b64decode(docx_base64)
                    dest_name = dest_name_pattern.format(index=index)
                    docx_path = Path(output_dir) / dest_name

                    with open(docx_path, "wb") as f:
                        f.write(docx_bytes)

                    processed_result["docx_path"] = str(docx_path)
                    logger.debug(f"Saved bulk result {index} to {docx_path}")
                except Exception as e:
                    logger.warning(f"Failed to save bulk result {index}: {e}")
                    processed_result["status"] = "error"
                    processed_result["error"] = f"Failed to save DOCX: {e}"
            elif error:
                processed_result["error"] = error

            processed_results.append(processed_result)

        # Build response dict
        result_dict = {
            "results": processed_results,
            "total": response.get("total", len(plaintexts)),
            "successful": response.get("successful", 0),
            "failed": response.get("failed", 0),
            "processing_time_seconds": response.get("processing_time_seconds", 0),
            "metered_count": response.get("metered_count", len(plaintexts)),
        }

        # Save bulk run manifest to workspace
        try:
            schema_str = json.dumps(schema, sort_keys=True)
            schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]

            manifest = {
                "timestamp": datetime.now().isoformat(),
                "schema_hash": schema_hash,
                "plaintexts_count": len(plaintexts),
                "max_concurrent": max_concurrent,
                "dest_name_pattern": dest_name_pattern,
                **result_dict,
            }

            manifest_path = ws.save_json("output_configs", "bulk_run_manifest", manifest)
            logger.info(f"Bulk run manifest saved to {manifest_path}")
        except Exception as e:
            logger.warning(f"Failed to save bulk run manifest: {e}")

        logger.info(
            f"Bulk schema run completed: {result_dict['successful']} successful, "
            f"{result_dict['failed']} failed"
        )
        return result_dict

    # -------------------------------------------------------------------------
    # Schema Compression
    # -------------------------------------------------------------------------

    def compress_schema(
        self,
        ws: Any,  # Workspace type
        *,
        schema: Dict[str, Any],
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compress a schema by deduplicating redundant pattern descriptors.

        Many schemas have redundant pattern descriptor types (e.g., "H-SHORT" appearing
        multiple times with the same styles and properties). This endpoint compresses
        the schema by grouping pattern descriptors by type and selecting the highest
        scoring descriptor for each type.

        Endpoint: POST /schema/compress

        Args:
            ws: Workspace instance
            schema: Schema dict to compress (from build_schema_from_docx or loaded JSON)
            save_as: Optional name to save compressed schema JSON (without .json extension)

        Returns:
            Dict containing:
                - compressed_schema: The compressed schema with deduplicated pattern descriptors
                - stats: Compression statistics (original_count, compressed_count, reduction, etc.)

        Raises:
            ForgeClientIOError: Network/connection errors
            ForgeClientHTTPError: API returned non-2xx status (401, 403, 429)
            ForgeClientError: Failed to compress schema or save to workspace

        Example:
            >>> result = client.compress_schema(
            ...     ws,
            ...     schema=schema,
            ...     save_as="compressed_schema"
            ... )
            >>> print(f"Reduced from {result['stats']['original_count']} to {result['stats']['compressed_count']}")
            >>> compressed_schema = result['compressed_schema']
        """
        logger.info(f"Compressing schema, save_as={save_as}")

        response = self._make_request(
            "POST",
            "/schema/compress",
            json_data={"schema": schema},
        )

        compressed_schema = response.get("compressed_schema")
        stats = response.get("stats", {})

        if not compressed_schema:
            raise ForgeClientError(
                "Missing 'compressed_schema' in API response",
                endpoint="/schema/compress",
            )

        # Save compressed schema to workspace if requested
        if save_as:
            try:
                schema_path = ws.save_json("output_configs", save_as, compressed_schema)
                logger.info(f"Compressed schema saved to {schema_path}")
            except Exception as e:
                raise ForgeClientError(
                    f"Failed to save compressed schema to workspace: {e}",
                    endpoint="/schema/compress",
                ) from e

        logger.info(
            f"Schema compression completed: {stats.get('original_count', 'N/A')} -> "
            f"{stats.get('compressed_count', 'N/A')} pattern descriptors "
            f"({stats.get('reduction_percentage', 0):.1f}% reduction)"
        )

        return {
            "compressed_schema": compressed_schema,
            "stats": stats,
        }

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
        # Mask API key for security (show only first 8 chars)
        masked_key = f"{self.api_key[:8]}..." if len(self.api_key) > 8 else "***"
        return f"ForgeClient(base_url={self.base_url!r}, api_key={masked_key!r}, timeout={self.timeout})"