# glyph_forge/core/client/forge_client.py
"""
ForgeClient: Local SDK-based client for Glyph Forge.

Uses the Glyph SDK directly for local schema building and running.
No API calls - everything runs locally.
"""

from __future__ import annotations

import logging
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List
from datetime import datetime

from .exceptions import ForgeClientError, ForgeClientIOError, ForgeClientHTTPError

# Import SDK components from submodule
from glyph.core.utils.docx_intake import intake_docx
from glyph.core.schema.build_schema import GlyphSchemaBuilder
from glyph.core.schema_runner.run_schema import GlyphSchemaRunner

# Import local compression utilities
from glyph_forge.core.compression import compress_schema as compress_schema_fn, get_compression_stats

# Import httpx for API calls (optional dependency)
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False


logger = logging.getLogger(__name__)


class ForgeClient:
    """
    Local SDK-based client for Glyph Forge.

    Uses the Glyph SDK directly to build and run schemas locally.
    No API key required - all processing happens on your machine.

    Args:
        api_key: Deprecated. No longer used (kept for backwards compatibility).
        base_url: Deprecated. No longer used (kept for backwards compatibility).
        timeout: Deprecated. No longer used (kept for backwards compatibility).

    Example:
        >>> from glyph_forge import ForgeClient, create_workspace
        >>> ws = create_workspace()
        >>> client = ForgeClient()
        >>> schema = client.build_schema_from_docx(ws, docx_path="sample.docx")
    """

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
            api_key: API key for Glyph Forge API (for /ask endpoint and other API calls)
            base_url: Base URL for API (default: https://dev.glyphapi.ai)
            timeout: Request timeout in seconds (default: 30.0)
        """
        # Store params
        self.api_key = api_key or os.getenv("GLYPH_API_KEY")
        self.base_url = base_url or os.getenv("GLYPH_API_BASE") or "https://dev.glyphapi.ai"
        self.timeout = timeout

        # HTTP client for API calls (lazy initialization)
        self._http_client: Optional[httpx.Client] = None

        # Log initialization
        logger.info(f"ForgeClient initialized (local SDK mode + API support)")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # type: ignore
        self.close()
        return False

    def close(self):
        """Close the client and cleanup resources."""
        if self._http_client:
            self._http_client.close()
            self._http_client = None

    def _get_http_client(self) -> httpx.Client:
        """Get or create HTTP client for API calls."""
        if not HTTPX_AVAILABLE:
            raise ForgeClientError(
                "httpx is required for API calls. Install with: pip install httpx",
                endpoint="API"
            )

        if self._http_client is None:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._http_client = httpx.Client(
                base_url=self.base_url.rstrip("/"),
                headers=headers,
                timeout=self.timeout
            )

        return self._http_client

    def build_schema_from_docx(
        self,
        ws: Any,  # Workspace type from glyph.core.workspace
        *,
        docx_path: str,
        save_as: Optional[str] = None,
        include_artifacts: bool = False,
    ) -> Dict[str, Any]:
        """
        Build a schema from a DOCX file using the local SDK.

        Args:
            ws: Workspace instance for saving artifacts
            docx_path: Path to DOCX file (absolute or CWD-relative)
            save_as: Optional name to save schema JSON (without .json extension)
            include_artifacts: If True, save tagged DOCX + unzipped files (default: False)

        Returns:
            Schema dict

        Raises:
            ForgeClientError: File not found or processing error

        Example:
            >>> schema = client.build_schema_from_docx(
            ...     ws,
            ...     docx_path="sample.docx",
            ...     save_as="my_schema"
            ... )
        """
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

        try:
            # Use SDK to intake and extract DOCX
            intake_result = intake_docx(docx_abs, ws)

            # Get document.xml path
            document_xml = intake_result.key_files.get("document_xml")
            if not document_xml:
                raise ForgeClientError(
                    f"Failed to extract document.xml from DOCX",
                    endpoint="/schema/build",
                )

            # Build schema using SDK
            builder = GlyphSchemaBuilder(
                document_xml_path=str(document_xml),
                docx_extract_dir=str(intake_result.unzip_dir),
                source_docx=str(intake_result.stored_docx_path),
                tag=ws.tag if hasattr(ws, 'tag') else None
            )

            schema = builder.run()

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

            logger.info(
                f"Schema built successfully: "
                f"{len(schema.get('fields', []))} fields, "
                f"{len(schema.get('pattern_descriptors', []))} pattern descriptors"
            )

            return schema

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to build schema: {e}",
                endpoint="/schema/build",
            ) from e

    def run_schema(
        self,
        ws: Any,  # Workspace type
        *,
        schema: Dict[str, Any],
        plaintext: str,
        dest_name: str = "assembled_output.docx",
    ) -> str:
        """
        Run a schema with plaintext to generate a DOCX using the local SDK.

        Args:
            ws: Workspace instance
            schema: Schema dict (from build_schema_from_docx or loaded JSON)
            plaintext: Input text content
            dest_name: Name for output DOCX file (saved in output_docx directory)

        Returns:
            Local path to saved DOCX file

        Raises:
            ForgeClientError: Failed to run schema or save DOCX

        Example:
            >>> docx_path = client.run_schema(
            ...     ws,
            ...     schema=schema,
            ...     plaintext="Sample text...",
            ...     dest_name="output.docx"
            ... )
        """
        logger.info(f"Running schema with plaintext length={len(plaintext)}, dest_name={dest_name}")

        try:
            # Create SDK runner
            runner = GlyphSchemaRunner(schema)

            # Run with plaintext
            runner.run_with_plaintext(plaintext)

            # Save DOCX to workspace
            output_dir = ws.directory("output_docx")
            docx_path = Path(output_dir) / dest_name

            runner.document.save(str(docx_path))
            logger.info(f"DOCX saved to {docx_path}")

        except Exception as e:
            raise ForgeClientError(
                f"Failed to run schema: {e}",
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
                "status": "success",
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
        Run a schema with multiple plaintexts to generate multiple DOCX files.

        Args:
            ws: Workspace instance
            schema: Schema dict (from build_schema_from_docx or loaded JSON)
            plaintexts: List of plaintext strings to process
            max_concurrent: Ignored in local SDK mode (processed sequentially)
            dest_name_pattern: Pattern for output filenames. Use {index} placeholder

        Returns:
            Dict containing results with status, paths, and timing info

        Example:
            >>> result = client.run_schema_bulk(
            ...     ws,
            ...     schema=schema,
            ...     plaintexts=["Text 1...", "Text 2...", "Text 3..."],
            ...     dest_name_pattern="invoice_{index}.docx"
            ... )
        """
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

        logger.info(f"Running schema in bulk with {len(plaintexts)} plaintexts")

        start_time = datetime.now()
        results = []
        successful = 0
        failed = 0

        output_dir = ws.directory("output_docx")

        for index, plaintext in enumerate(plaintexts):
            result = {
                "index": index,
            }

            try:
                # Run schema for this plaintext
                runner = GlyphSchemaRunner(schema)
                runner.run_with_plaintext(plaintext)

                # Save DOCX
                dest_name = dest_name_pattern.format(index=index)
                docx_path = Path(output_dir) / dest_name
                runner.document.save(str(docx_path))

                result["status"] = "success"
                result["docx_path"] = str(docx_path)
                successful += 1
                logger.debug(f"Saved bulk result {index} to {docx_path}")

            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
                failed += 1
                logger.warning(f"Failed to process bulk item {index}: {e}")

            results.append(result)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Build response dict
        result_dict = {
            "results": results,
            "total": len(plaintexts),
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": processing_time,
            "metered_count": len(plaintexts),
        }

        # Save bulk run manifest
        try:
            schema_str = json.dumps(schema, sort_keys=True)
            schema_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]

            manifest = {
                "timestamp": datetime.now().isoformat(),
                "schema_hash": schema_hash,
                "plaintexts_count": len(plaintexts),
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

    def compress_schema(
        self,
        ws: Any,  # Workspace type
        *,
        schema: Dict[str, Any],
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compress a schema by deduplicating redundant pattern descriptors.

        Args:
            ws: Workspace instance
            schema: Schema dict to compress
            save_as: Optional name to save compressed schema JSON

        Returns:
            Dict containing compressed_schema and stats

        Example:
            >>> result = client.compress_schema(
            ...     ws,
            ...     schema=schema,
            ...     save_as="compressed_schema"
            ... )
        """
        logger.info(f"Compressing schema, save_as={save_as}")

        try:
            # Use SDK compress function
            compressed_schema = compress_schema_fn(schema)
            stats = get_compression_stats(schema, compressed_schema)

            # Save compressed schema if requested
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

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to compress schema: {e}",
                endpoint="/schema/compress",
            ) from e

    def intake_plaintext_text(
        self,
        ws: Any,  # Workspace type
        *,
        text: str,
        save_as: Optional[str] = None,
        **opts: Any,
    ) -> Dict[str, Any]:
        """
        Intake plaintext via text string (local processing).

        Args:
            ws: Workspace instance
            text: Plaintext content to intake
            save_as: Optional name to save intake result JSON
            **opts: Additional options (unicode_form, strip_zero_width, etc.)

        Returns:
            Intake result dict

        Example:
            >>> result = client.intake_plaintext_text(
            ...     ws,
            ...     text="Sample text...",
            ...     save_as="intake_result"
            ... )
        """
        logger.info(f"Intaking plaintext (text length={len(text)}), save_as={save_as}")

        try:
            from glyph.core.utils.plaintext_intake import intake_plaintext

            result = intake_plaintext(text, **opts)

            # Save to workspace if requested
            if save_as:
                try:
                    result_path = ws.save_json("output_configs", save_as, result)
                    logger.info(f"Intake result saved to {result_path}")
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save intake result to workspace: {e}",
                        endpoint="/plaintext/intake",
                    ) from e

            return result

        except Exception as e:
            raise ForgeClientError(
                f"Failed to intake plaintext: {e}",
                endpoint="/plaintext/intake",
            ) from e

    def intake_plaintext_file(
        self,
        ws: Any,  # Workspace type
        *,
        file_path: str,
        save_as: Optional[str] = None,
        **opts: Any,
    ) -> Dict[str, Any]:
        """
        Intake plaintext from file (local processing).

        Args:
            ws: Workspace instance
            file_path: Path to plaintext file
            save_as: Optional name to save intake result JSON
            **opts: Additional options

        Returns:
            Intake result dict

        Example:
            >>> result = client.intake_plaintext_file(
            ...     ws,
            ...     file_path="sample.txt",
            ...     save_as="intake_result"
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

        try:
            # Read file
            with open(file_abs, "r", encoding="utf-8") as f:
                text = f.read()

            # Use text intake
            return self.intake_plaintext_text(ws, text=text, save_as=save_as, **opts)

        except ForgeClientError:
            raise
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read file {file_abs}: {e}",
                endpoint="/plaintext/intake_file",
            ) from e

    def ask(
        self,
        *,
        message: str,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        current_schema: Optional[Dict[str, Any]] = None,
        current_plaintext: Optional[str] = None,
        current_document: Optional[Dict[str, Any]] = None,
        real_time: bool = False,
        strict_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a message to the Glyph Agent multi-agent system via API.

        This endpoint orchestrates:
        1. Intent classification
        2. Agent routing (schema, plaintext, validation, conversation)
        3. Multi-step workflows
        4. Markup application
        5. Conversation state management

        Args:
            message: The message to send to the agent (required)
            tenant_id: Tenant identifier for rate limiting
            user_id: User identifier for rate limiting
            conversation_id: Conversation ID for context tracking
            conversation_history: Previous conversation messages for context
                                 List of dicts with 'role' and 'content' keys
            current_schema: Current schema state (for incremental modifications)
            current_plaintext: Current plaintext content (for incremental modifications)
            current_document: Legacy combined document state
            real_time: Enable real-time sandbox updates
            strict_validation: Enable strict validation mode

        Returns:
            Dict containing:
            - response: The agent's response message
            - document: Generated or modified document (if applicable)
            - schema/document_schema: Document schema (if schema request)
            - plaintext: Generated plaintext content
            - validation_result: Validation results (if validation request)
            - metadata: Additional metadata (intent, routing, etc.)
            - usage: Token usage information
            - conversation_id: Conversation ID for tracking

        Raises:
            ForgeClientError: Missing API key or request failed
            ForgeClientHTTPError: HTTP error from API
            ForgeClientIOError: Network or connection error

        Example:
            >>> client = ForgeClient(api_key="your-api-key")
            >>> response = client.ask(
            ...     message="Create a schema for a quarterly report",
            ...     user_id="user123"
            ... )
            >>> print(response['response'])
            >>> if 'schema' in response:
            ...     print(f"Schema generated: {len(response['schema']['pattern_descriptors'])} descriptors")
        """
        if not self.api_key:
            raise ForgeClientError(
                "API key required for /ask endpoint. "
                "Provide api_key parameter or set GLYPH_API_KEY environment variable.",
                endpoint="/glyph_agent/ask"
            )

        logger.info(f"Sending message to /glyph_agent/ask: {message[:100]}...")

        # Build request payload
        payload: Dict[str, Any] = {
            "message": message,
        }

        # Add optional parameters
        if tenant_id:
            payload["tenant_id"] = tenant_id
        if user_id:
            payload["user_id"] = user_id
        if conversation_id:
            payload["conversation_id"] = conversation_id
        if conversation_history:
            payload["conversation_history"] = conversation_history
        if current_schema:
            payload["current_schema"] = current_schema
        if current_plaintext:
            payload["current_plaintext"] = current_plaintext
        if current_document:
            payload["current_document"] = current_document
        if real_time:
            payload["real_time"] = real_time
        if strict_validation:
            payload["strict_validation"] = strict_validation

        try:
            client = self._get_http_client()
            response = client.post("/glyph_agent/ask", json=payload)

            # Check for HTTP errors
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", response.text)
                except Exception:
                    pass

                raise ForgeClientHTTPError(
                    f"API request failed",
                    status_code=response.status_code,
                    response_body=error_detail,
                    endpoint="/glyph_agent/ask"
                )

            # Parse response
            result = response.json()

            logger.info(
                f"Agent response received: {len(result.get('response', ''))} chars, "
                f"usage: {result.get('usage', {}).get('total_tokens', 'N/A')} tokens"
            )

            return result

        except ForgeClientHTTPError:
            raise
        except httpx.RequestError as e:
            raise ForgeClientIOError(
                f"Network error during /ask request: {e}",
                endpoint="/glyph_agent/ask",
                original_error=e
            ) from e
        except Exception as e:
            raise ForgeClientError(
                f"Failed to call /ask endpoint: {e}",
                endpoint="/glyph_agent/ask",
            ) from e

    def __repr__(self) -> str:
        return f"ForgeClient(mode='local-sdk')"
