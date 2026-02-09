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
        classify: bool = False,
        save_as: Optional[str] = None,
        **opts: Any,
    ) -> Dict[str, Any]:
        """
        Intake plaintext via text string (local processing).

        Args:
            ws: Workspace instance
            text: Plaintext content to intake
            classify: If True, run heuristic classification on each line
                      (adds ``classifications`` key to the result)
            save_as: Optional name to save intake result JSON
            **opts: Additional options (unicode_form, strip_zero_width, etc.)

        Returns:
            Intake result dict

        Example:
            >>> result = client.intake_plaintext_text(
            ...     ws,
            ...     text="Sample text...",
            ...     classify=True,
            ...     save_as="intake_result"
            ... )
        """
        logger.info(f"Intaking plaintext (text length={len(text)}, classify={classify}), save_as={save_as}")

        try:
            from glyph.core.utils.plaintext_intake import intake_plaintext

            result = intake_plaintext(text, **opts)

            # Run heuristic classification if requested
            if classify:
                from glyph.core.analysis.plaintext.classifier import classify_lines as _classify_lines
                import dataclasses
                classifications = _classify_lines(result.lines)
                object.__setattr__(result, "line_patterns", [
                    dataclasses.asdict(c) for c in classifications
                ])

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

    # ------------------------------------------------------------------
    # Form Detection
    # ------------------------------------------------------------------

    def detect_forms(
        self,
        ws: Any,  # Workspace type
        *,
        text: str,
        forms: Optional[List[str]] = None,
        threshold: float = 0.55,
        use_context: bool = True,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect heuristic forms (headings, lists, paragraphs, etc.) in plaintext.

        Runs the SDK's line classifier against each line and returns
        classifications filtered by form type and confidence threshold.

        Args:
            ws: Workspace instance
            text: Plaintext content to classify
            forms: Optional list of form codes to keep
                   (e.g. ``["H-SHORT", "L-BULLET"]``). ``None`` returns all.
            threshold: Minimum confidence score (0.0–1.0, default 0.55)
            use_context: Use surrounding-line context for better accuracy
            save_as: Optional name to save result JSON in workspace

        Returns:
            Dict with keys ``classifications``, ``total_lines``,
            ``matched_lines``, ``forms_filter``, ``threshold``.

        Example:
            >>> result = client.detect_forms(
            ...     ws,
            ...     text=open("doc.txt").read(),
            ...     forms=["H-SHORT", "L-BULLET"],
            ... )
            >>> for c in result["classifications"]:
            ...     print(c["pattern_type"], c["text"][:60])
        """
        logger.info(
            f"Detecting forms (text length={len(text)}, forms={forms}, "
            f"threshold={threshold}, use_context={use_context})"
        )

        try:
            from glyph.core.analysis.plaintext.classifier import classify_lines
            import dataclasses

            lines = text.splitlines()
            raw = classify_lines(lines, use_context=use_context)

            # Filter by threshold and form codes
            matched = []
            for c in raw:
                if c.score < threshold:
                    continue
                if forms and c.pattern_type not in forms:
                    continue
                matched.append(dataclasses.asdict(c))

            result: Dict[str, Any] = {
                "classifications": matched,
                "total_lines": len(lines),
                "matched_lines": len(matched),
                "forms_filter": forms,
                "threshold": threshold,
            }

            if save_as:
                try:
                    ws.save_json("output_configs", save_as, result)
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save detect_forms result: {e}",
                        endpoint="/detect/forms",
                    ) from e

            logger.info(f"Form detection complete: {len(matched)}/{len(lines)} lines matched")
            return result

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to detect forms: {e}",
                endpoint="/detect/forms",
            ) from e

    def detect_forms_file(
        self,
        ws: Any,  # Workspace type
        *,
        file_path: str,
        forms: Optional[List[str]] = None,
        threshold: float = 0.55,
        use_context: bool = True,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect heuristic forms in a plaintext file.

        Reads the file and delegates to :meth:`detect_forms`.

        Args:
            ws: Workspace instance
            file_path: Path to plaintext file
            forms: Optional form-code filter list
            threshold: Minimum confidence score
            use_context: Use surrounding-line context
            save_as: Optional name to save result JSON

        Returns:
            Same dict as :meth:`detect_forms`
        """
        file_abs = Path(file_path).resolve()
        if not file_abs.exists():
            raise ForgeClientError(f"File not found: {file_abs}", endpoint="/detect/forms")
        if not file_abs.is_file():
            raise ForgeClientError(f"Not a file: {file_abs}", endpoint="/detect/forms")

        try:
            with open(file_abs, "r", encoding="utf-8") as f:
                text = f.read()
            return self.detect_forms(
                ws, text=text, forms=forms, threshold=threshold,
                use_context=use_context, save_as=save_as,
            )
        except ForgeClientError:
            raise
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read file {file_abs}: {e}",
                endpoint="/detect/forms",
            ) from e

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def chunk_plaintext_text(
        self,
        ws: Any,  # Workspace type
        *,
        text: str,
        threshold: float = 0.55,
        heading_forms: Optional[List[str]] = None,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Split plaintext into heading-bounded chunks.

        Runs heading detection on each line and splits the text at
        heading boundaries so each chunk can be processed independently
        (e.g. fed to an LLM one section at a time).

        Args:
            ws: Workspace instance
            text: Plaintext content to chunk
            threshold: Heading-detection confidence threshold (default 0.55)
            heading_forms: Optional list of heading forms to split on
                           (e.g. ``["H-SHORT", "H-SECTION-N"]``). ``None`` uses all.
            save_as: Optional name to save result JSON

        Returns:
            Dict with keys ``chunks`` (list), ``total_chunks``,
            ``total_lines``, ``headings_detected``.

        Example:
            >>> result = client.chunk_plaintext_text(
            ...     ws, text=open("doc.txt").read()
            ... )
            >>> for chunk in result["chunks"]:
            ...     print(chunk["heading_text"], "->", len(chunk["plaintext"]), "chars")
        """
        logger.info(
            f"Chunking plaintext (text length={len(text)}, threshold={threshold}, "
            f"heading_forms={heading_forms})"
        )

        try:
            from glyph.core.analysis.detectors.heuristics.heading_detector import detect_headings

            lines = text.splitlines()
            detections = detect_headings(lines, threshold=threshold)

            # Filter by heading forms if specified
            if heading_forms:
                detections = [
                    d for d in detections
                    if d.form is not None and d.form.value in heading_forms
                ]

            # Build chunks from heading boundaries
            chunks: List[Dict[str, Any]] = []
            heading_indices = [d.line_idx for d in detections]
            detection_map = {d.line_idx: d for d in detections}

            # Determine split points
            if not heading_indices:
                # No headings — single preamble chunk
                chunks.append({
                    "chunk_id": "chunk_0",
                    "heading_text": "",
                    "heading_form": None,
                    "heading_level": None,
                    "heading_score": 0.0,
                    "plaintext": text,
                    "line_start": 0,
                    "line_end": len(lines),
                })
            else:
                # Preamble before first heading
                if heading_indices[0] > 0:
                    preamble_lines = lines[: heading_indices[0]]
                    preamble_text = "\n".join(preamble_lines)
                    if preamble_text.strip():
                        chunks.append({
                            "chunk_id": f"chunk_{len(chunks)}",
                            "heading_text": "",
                            "heading_form": None,
                            "heading_level": None,
                            "heading_score": 0.0,
                            "plaintext": preamble_text,
                            "line_start": 0,
                            "line_end": heading_indices[0],
                        })

                # Each heading starts a new chunk
                for i, h_idx in enumerate(heading_indices):
                    end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines)
                    det = detection_map[h_idx]
                    chunk_lines = lines[h_idx:end_idx]
                    chunks.append({
                        "chunk_id": f"chunk_{len(chunks)}",
                        "heading_text": det.clean_text or lines[h_idx],
                        "heading_form": det.form.value if det.form else None,
                        "heading_level": det.level,
                        "heading_score": det.score,
                        "plaintext": "\n".join(chunk_lines),
                        "line_start": h_idx,
                        "line_end": end_idx,
                    })

            result: Dict[str, Any] = {
                "chunks": chunks,
                "total_chunks": len(chunks),
                "total_lines": len(lines),
                "headings_detected": len(detections),
            }

            if save_as:
                try:
                    ws.save_json("output_configs", save_as, result)
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save chunk result: {e}",
                        endpoint="/chunk/text",
                    ) from e

            logger.info(f"Chunking complete: {len(chunks)} chunks from {len(lines)} lines")
            return result

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to chunk plaintext: {e}",
                endpoint="/chunk/text",
            ) from e

    def chunk_plaintext_file(
        self,
        ws: Any,  # Workspace type
        *,
        file_path: str,
        threshold: float = 0.55,
        heading_forms: Optional[List[str]] = None,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Split a plaintext file into heading-bounded chunks.

        Reads the file and delegates to :meth:`chunk_plaintext_text`.

        Args:
            ws: Workspace instance
            file_path: Path to plaintext file
            threshold: Heading-detection confidence threshold
            heading_forms: Optional heading-form filter list
            save_as: Optional name to save result JSON

        Returns:
            Same dict as :meth:`chunk_plaintext_text`
        """
        file_abs = Path(file_path).resolve()
        if not file_abs.exists():
            raise ForgeClientError(f"File not found: {file_abs}", endpoint="/chunk/text")
        if not file_abs.is_file():
            raise ForgeClientError(f"Not a file: {file_abs}", endpoint="/chunk/text")

        try:
            with open(file_abs, "r", encoding="utf-8") as f:
                text = f.read()
            return self.chunk_plaintext_text(
                ws, text=text, threshold=threshold,
                heading_forms=heading_forms, save_as=save_as,
            )
        except ForgeClientError:
            raise
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read file {file_abs}: {e}",
                endpoint="/chunk/text",
            ) from e

    def chunk_docx(
        self,
        ws: Any,  # Workspace type
        *,
        docx_path: str,
        threshold: float = 0.55,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Chunk a DOCX document into heading-bounded sections.

        Extracts paragraph text from the DOCX, detects headings via
        heuristics, and splits into chunks. Each chunk includes the
        heading metadata and the plaintext content of that section.

        Args:
            ws: Workspace instance
            docx_path: Path to DOCX file
            threshold: Heading-detection confidence threshold (default 0.55)
            save_as: Optional name to save result JSON

        Returns:
            Dict with keys ``chunks``, ``total_chunks``,
            ``total_paragraphs``, ``headings_detected``.

        Example:
            >>> result = client.chunk_docx(ws, docx_path="report.docx")
            >>> for chunk in result["chunks"]:
            ...     print(chunk["heading_text"], "->", len(chunk["plaintext"]), "chars")
        """
        logger.info(f"Chunking DOCX: {docx_path}, threshold={threshold}")

        docx_abs = Path(docx_path).resolve()
        if not docx_abs.exists():
            raise ForgeClientError(f"DOCX file not found: {docx_abs}", endpoint="/chunk/docx")
        if not docx_abs.is_file():
            raise ForgeClientError(f"Not a file: {docx_abs}", endpoint="/chunk/docx")

        try:
            # Intake DOCX to extract document.xml
            intake_result = intake_docx(docx_abs, ws)
            document_xml = intake_result.key_files.get("document_xml")
            if not document_xml:
                raise ForgeClientError(
                    "Failed to extract document.xml from DOCX",
                    endpoint="/chunk/docx",
                )

            # Parse paragraph texts from document.xml
            from xml.etree import ElementTree as ET

            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            tree = ET.parse(str(document_xml))
            root = tree.getroot()
            body = root.find("w:body", ns)
            if body is None:
                raise ForgeClientError(
                    "No <w:body> found in document.xml",
                    endpoint="/chunk/docx",
                )

            paragraphs: List[str] = []
            for p_elem in body.findall("w:p", ns):
                runs = p_elem.findall(".//w:r/w:t", ns)
                text = "".join(r.text or "" for r in runs)
                paragraphs.append(text)

            # Detect headings
            from glyph.core.analysis.detectors.heuristics.heading_detector import detect_headings
            detections = detect_headings(paragraphs, threshold=threshold)

            # Build chunks (same algorithm as chunk_plaintext_text)
            chunks: List[Dict[str, Any]] = []
            heading_indices = [d.line_idx for d in detections]
            detection_map = {d.line_idx: d for d in detections}

            if not heading_indices:
                full_text = "\n".join(paragraphs)
                chunks.append({
                    "chunk_id": "chunk_0",
                    "heading_text": "",
                    "heading_form": None,
                    "heading_level": None,
                    "heading_score": 0.0,
                    "plaintext": full_text,
                    "paragraph_start": 0,
                    "paragraph_end": len(paragraphs),
                })
            else:
                if heading_indices[0] > 0:
                    preamble = "\n".join(paragraphs[: heading_indices[0]])
                    if preamble.strip():
                        chunks.append({
                            "chunk_id": f"chunk_{len(chunks)}",
                            "heading_text": "",
                            "heading_form": None,
                            "heading_level": None,
                            "heading_score": 0.0,
                            "plaintext": preamble,
                            "paragraph_start": 0,
                            "paragraph_end": heading_indices[0],
                        })

                for i, h_idx in enumerate(heading_indices):
                    end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(paragraphs)
                    det = detection_map[h_idx]
                    chunk_text = "\n".join(paragraphs[h_idx:end_idx])
                    chunks.append({
                        "chunk_id": f"chunk_{len(chunks)}",
                        "heading_text": det.clean_text or paragraphs[h_idx],
                        "heading_form": det.form.value if det.form else None,
                        "heading_level": det.level,
                        "heading_score": det.score,
                        "plaintext": chunk_text,
                        "paragraph_start": h_idx,
                        "paragraph_end": end_idx,
                    })

            result: Dict[str, Any] = {
                "chunks": chunks,
                "total_chunks": len(chunks),
                "total_paragraphs": len(paragraphs),
                "headings_detected": len(detections),
            }

            if save_as:
                try:
                    ws.save_json("output_configs", save_as, result)
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save chunk result: {e}",
                        endpoint="/chunk/docx",
                    ) from e

            logger.info(
                f"DOCX chunking complete: {len(chunks)} chunks "
                f"from {len(paragraphs)} paragraphs"
            )
            return result

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to chunk DOCX: {e}",
                endpoint="/chunk/docx",
            ) from e

    # ------------------------------------------------------------------
    # Document Indexing
    # ------------------------------------------------------------------

    def index_document(
        self,
        ws: Any,  # Workspace type
        *,
        text: str,
        section_forms: Optional[List[str]] = None,
        annotate_forms: Optional[List[str]] = None,
        threshold: float = 0.55,
        use_context: bool = True,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a structured document index with heading-bounded sections
        and optional form-annotated segments.

        Combines heading detection (for section boundaries) with line
        classification (for segment annotation) to produce an index
        that lets you request specific form types AND get the content
        between reference points.

        Args:
            ws: Workspace instance
            text: Plaintext content to index
            section_forms: Heading form codes that define section boundaries
                           (e.g. ``["H-SHORT", "H-SECTION-N"]``).
                           ``None`` uses all heading forms.
            annotate_forms: Form codes to annotate as segments within sections
                            (e.g. ``["L-BULLET", "T-ROW"]``).
                            ``None`` skips classification entirely (faster).
                            ``[]`` runs classification but matches nothing.
            threshold: Minimum confidence score (0.0–1.0, default 0.55)
            use_context: Use surrounding-line context for classification
            save_as: Optional name to save result JSON in workspace

        Returns:
            Dict with keys ``sections``, ``preamble``, ``total_sections``,
            ``total_lines``, ``headings_detected``, ``section_forms``,
            ``annotate_forms``.

        Example:
            >>> result = client.index_document(
            ...     ws,
            ...     text=open("doc.txt").read(),
            ...     annotate_forms=["L-BULLET", "T-ROW"],
            ... )
            >>> for sec in result["sections"]:
            ...     print(sec["heading"]["text"], len(sec["segments"]), "segments")
        """
        logger.info(
            f"Indexing document (text length={len(text)}, section_forms={section_forms}, "
            f"annotate_forms={annotate_forms}, threshold={threshold})"
        )

        try:
            from glyph.core.analysis.detectors.heuristics.heading_detector import detect_headings
            from glyph.core.analysis.forms.headings import HeadingForm

            lines = text.splitlines()

            # Detect headings
            detections = detect_headings(lines, threshold=threshold)

            # Default section_forms to all HeadingForm values
            if section_forms is None:
                section_forms = [f.value for f in HeadingForm]

            # Filter detections by section_forms
            detections = [
                d for d in detections
                if d.form is not None and d.form.value in section_forms
            ]

            # Optionally classify lines for segment annotation
            classifications = None
            if annotate_forms is not None:
                from glyph.core.analysis.plaintext.classifier import classify_lines
                classifications = classify_lines(lines, use_context=use_context)

            # Build section boundaries
            heading_indices = [d.line_idx for d in detections]
            detection_map = {d.line_idx: d for d in detections}

            # Helper: group contiguous lines matching annotate_forms into segments
            def _build_segments(start: int, end: int) -> List[Dict[str, Any]]:
                if classifications is None or annotate_forms is None:
                    return []
                segments: List[Dict[str, Any]] = []
                current_form: Optional[str] = None
                seg_start: int = 0
                seg_lines: List[str] = []

                for idx in range(start, end):
                    c = classifications[idx]
                    if c.pattern_type in annotate_forms and c.score >= threshold:
                        if c.pattern_type == current_form:
                            # Extend current segment
                            seg_lines.append(c.text)
                        else:
                            # Close previous segment if any
                            if current_form is not None:
                                segments.append({
                                    "form": current_form,
                                    "span": {"start": seg_start, "end": idx - 1},
                                    "content": "\n".join(seg_lines),
                                    "count": len(seg_lines),
                                })
                            # Start new segment
                            current_form = c.pattern_type
                            seg_start = idx
                            seg_lines = [c.text]
                    else:
                        # Non-matching line closes current segment
                        if current_form is not None:
                            segments.append({
                                "form": current_form,
                                "span": {"start": seg_start, "end": idx - 1},
                                "content": "\n".join(seg_lines),
                                "count": len(seg_lines),
                            })
                            current_form = None
                            seg_lines = []

                # Finalize trailing segment
                if current_form is not None:
                    segments.append({
                        "form": current_form,
                        "span": {"start": seg_start, "end": end - 1},
                        "content": "\n".join(seg_lines),
                        "count": len(seg_lines),
                    })

                return segments

            # Build sections and preamble
            sections: List[Dict[str, Any]] = []
            preamble: Dict[str, Any]

            if not heading_indices:
                # No headings — everything goes to preamble
                preamble_text = "\n".join(lines)
                preamble = {
                    "span": {"start": 0, "end": len(lines)},
                    "content": preamble_text if preamble_text.strip() else "",
                    "segments": _build_segments(0, len(lines)),
                }
            else:
                # Preamble before first heading
                first_h = heading_indices[0]
                if first_h > 0:
                    preamble_text = "\n".join(lines[:first_h])
                    preamble = {
                        "span": {"start": 0, "end": first_h},
                        "content": preamble_text if preamble_text.strip() else "",
                        "segments": _build_segments(0, first_h),
                    }
                else:
                    preamble = {
                        "span": {"start": 0, "end": 0},
                        "content": "",
                        "segments": [],
                    }

                # Each heading starts a section
                for i, h_idx in enumerate(heading_indices):
                    end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(lines)
                    det = detection_map[h_idx]
                    section_lines = lines[h_idx:end_idx]
                    sections.append({
                        "section_id": f"sec_{i}",
                        "heading": {
                            "text": det.clean_text or lines[h_idx],
                            "form": det.form.value if det.form else None,
                            "line": h_idx,
                            "score": det.score,
                            "level": det.level,
                            "numbering": det.numbering,
                        },
                        "span": {"start": h_idx, "end": end_idx},
                        "content": "\n".join(section_lines),
                        "segments": _build_segments(h_idx, end_idx),
                    })

            result: Dict[str, Any] = {
                "sections": sections,
                "preamble": preamble,
                "total_sections": len(sections),
                "total_lines": len(lines),
                "headings_detected": len(detections),
                "section_forms": section_forms,
                "annotate_forms": annotate_forms,
            }

            if save_as:
                try:
                    ws.save_json("output_configs", save_as, result)
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save index result: {e}",
                        endpoint="/index/document",
                    ) from e

            logger.info(
                f"Document indexing complete: {len(sections)} sections, "
                f"{len(lines)} lines, {len(detections)} headings"
            )
            return result

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to index document: {e}",
                endpoint="/index/document",
            ) from e

    def index_document_file(
        self,
        ws: Any,  # Workspace type
        *,
        file_path: str,
        section_forms: Optional[List[str]] = None,
        annotate_forms: Optional[List[str]] = None,
        threshold: float = 0.55,
        use_context: bool = True,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a structured document index from a plaintext file.

        Reads the file and delegates to :meth:`index_document`.

        Args:
            ws: Workspace instance
            file_path: Path to plaintext file
            section_forms: Heading form codes for section boundaries
            annotate_forms: Form codes to annotate as segments
            threshold: Minimum confidence score
            use_context: Use surrounding-line context
            save_as: Optional name to save result JSON

        Returns:
            Same dict as :meth:`index_document`
        """
        file_abs = Path(file_path).resolve()
        if not file_abs.exists():
            raise ForgeClientError(f"File not found: {file_abs}", endpoint="/index/document")
        if not file_abs.is_file():
            raise ForgeClientError(f"Not a file: {file_abs}", endpoint="/index/document")

        try:
            with open(file_abs, "r", encoding="utf-8") as f:
                text = f.read()
            return self.index_document(
                ws, text=text, section_forms=section_forms,
                annotate_forms=annotate_forms, threshold=threshold,
                use_context=use_context, save_as=save_as,
            )
        except ForgeClientError:
            raise
        except OSError as e:
            raise ForgeClientError(
                f"Failed to read file {file_abs}: {e}",
                endpoint="/index/document",
            ) from e

    def index_docx(
        self,
        ws: Any,  # Workspace type
        *,
        docx_path: str,
        section_forms: Optional[List[str]] = None,
        annotate_forms: Optional[List[str]] = None,
        threshold: float = 0.55,
        use_context: bool = True,
        save_as: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a structured document index from a DOCX file.

        Extracts paragraph text from the DOCX, detects headings for
        section boundaries, and optionally annotates segments within
        each section.

        Args:
            ws: Workspace instance
            docx_path: Path to DOCX file
            section_forms: Heading form codes for section boundaries
            annotate_forms: Form codes to annotate as segments
            threshold: Minimum confidence score (default 0.55)
            use_context: Use surrounding-line context
            save_as: Optional name to save result JSON

        Returns:
            Dict with keys ``sections``, ``preamble``, ``total_sections``,
            ``total_paragraphs``, ``headings_detected``, ``section_forms``,
            ``annotate_forms``.

        Example:
            >>> result = client.index_docx(
            ...     ws,
            ...     docx_path="report.docx",
            ...     annotate_forms=["L-BULLET", "T-ROW"],
            ... )
        """
        logger.info(f"Indexing DOCX: {docx_path}, threshold={threshold}")

        docx_abs = Path(docx_path).resolve()
        if not docx_abs.exists():
            raise ForgeClientError(f"DOCX file not found: {docx_abs}", endpoint="/index/docx")
        if not docx_abs.is_file():
            raise ForgeClientError(f"Not a file: {docx_abs}", endpoint="/index/docx")

        try:
            # Intake DOCX to extract document.xml
            intake_result = intake_docx(docx_abs, ws)
            document_xml = intake_result.key_files.get("document_xml")
            if not document_xml:
                raise ForgeClientError(
                    "Failed to extract document.xml from DOCX",
                    endpoint="/index/docx",
                )

            # Parse paragraph texts from document.xml
            from xml.etree import ElementTree as ET

            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            tree = ET.parse(str(document_xml))
            root = tree.getroot()
            body = root.find("w:body", ns)
            if body is None:
                raise ForgeClientError(
                    "No <w:body> found in document.xml",
                    endpoint="/index/docx",
                )

            paragraphs: List[str] = []
            for p_elem in body.findall("w:p", ns):
                runs = p_elem.findall(".//w:r/w:t", ns)
                text = "".join(r.text or "" for r in runs)
                paragraphs.append(text)

            # Detect headings
            from glyph.core.analysis.detectors.heuristics.heading_detector import detect_headings
            from glyph.core.analysis.forms.headings import HeadingForm

            detections = detect_headings(paragraphs, threshold=threshold)

            # Default section_forms to all HeadingForm values
            if section_forms is None:
                section_forms = [f.value for f in HeadingForm]

            # Filter detections by section_forms
            detections = [
                d for d in detections
                if d.form is not None and d.form.value in section_forms
            ]

            # Optionally classify for segment annotation
            classifications = None
            if annotate_forms is not None:
                from glyph.core.analysis.plaintext.classifier import classify_lines
                classifications = classify_lines(paragraphs, use_context=use_context)

            # Build section boundaries
            heading_indices = [d.line_idx for d in detections]
            detection_map = {d.line_idx: d for d in detections}

            # Helper: group contiguous paragraphs matching annotate_forms
            def _build_segments(start: int, end: int) -> List[Dict[str, Any]]:
                if classifications is None or annotate_forms is None:
                    return []
                segments: List[Dict[str, Any]] = []
                current_form: Optional[str] = None
                seg_start: int = 0
                seg_lines: List[str] = []

                for idx in range(start, end):
                    c = classifications[idx]
                    if c.pattern_type in annotate_forms and c.score >= threshold:
                        if c.pattern_type == current_form:
                            seg_lines.append(c.text)
                        else:
                            if current_form is not None:
                                segments.append({
                                    "form": current_form,
                                    "span": {"start": seg_start, "end": idx - 1},
                                    "content": "\n".join(seg_lines),
                                    "count": len(seg_lines),
                                })
                            current_form = c.pattern_type
                            seg_start = idx
                            seg_lines = [c.text]
                    else:
                        if current_form is not None:
                            segments.append({
                                "form": current_form,
                                "span": {"start": seg_start, "end": idx - 1},
                                "content": "\n".join(seg_lines),
                                "count": len(seg_lines),
                            })
                            current_form = None
                            seg_lines = []

                if current_form is not None:
                    segments.append({
                        "form": current_form,
                        "span": {"start": seg_start, "end": end - 1},
                        "content": "\n".join(seg_lines),
                        "count": len(seg_lines),
                    })

                return segments

            # Build sections and preamble
            sections: List[Dict[str, Any]] = []
            preamble: Dict[str, Any]

            if not heading_indices:
                preamble_text = "\n".join(paragraphs)
                preamble = {
                    "span": {"start": 0, "end": len(paragraphs)},
                    "content": preamble_text if preamble_text.strip() else "",
                    "segments": _build_segments(0, len(paragraphs)),
                }
            else:
                first_h = heading_indices[0]
                if first_h > 0:
                    preamble_text = "\n".join(paragraphs[:first_h])
                    preamble = {
                        "span": {"start": 0, "end": first_h},
                        "content": preamble_text if preamble_text.strip() else "",
                        "segments": _build_segments(0, first_h),
                    }
                else:
                    preamble = {
                        "span": {"start": 0, "end": 0},
                        "content": "",
                        "segments": [],
                    }

                for i, h_idx in enumerate(heading_indices):
                    end_idx = heading_indices[i + 1] if i + 1 < len(heading_indices) else len(paragraphs)
                    det = detection_map[h_idx]
                    section_paras = paragraphs[h_idx:end_idx]
                    sections.append({
                        "section_id": f"sec_{i}",
                        "heading": {
                            "text": det.clean_text or paragraphs[h_idx],
                            "form": det.form.value if det.form else None,
                            "line": h_idx,
                            "score": det.score,
                            "level": det.level,
                            "numbering": det.numbering,
                        },
                        "span": {"start": h_idx, "end": end_idx},
                        "content": "\n".join(section_paras),
                        "segments": _build_segments(h_idx, end_idx),
                    })

            result: Dict[str, Any] = {
                "sections": sections,
                "preamble": preamble,
                "total_sections": len(sections),
                "total_paragraphs": len(paragraphs),
                "headings_detected": len(detections),
                "section_forms": section_forms,
                "annotate_forms": annotate_forms,
            }

            if save_as:
                try:
                    ws.save_json("output_configs", save_as, result)
                except Exception as e:
                    raise ForgeClientError(
                        f"Failed to save index result: {e}",
                        endpoint="/index/docx",
                    ) from e

            logger.info(
                f"DOCX indexing complete: {len(sections)} sections, "
                f"{len(paragraphs)} paragraphs, {len(detections)} headings"
            )
            return result

        except ForgeClientError:
            raise
        except Exception as e:
            raise ForgeClientError(
                f"Failed to index DOCX: {e}",
                endpoint="/index/docx",
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
