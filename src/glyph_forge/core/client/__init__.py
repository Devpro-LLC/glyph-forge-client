# glyph_forge/core/client/__init__.py
"""
Glyph Forge Client - Synchronous HTTP client for Glyph Forge API.

Public API:
    - ForgeClient: Main client class
    - ForgeClientError: Base exception
    - ForgeClientIOError: Network/connection errors
    - ForgeClientHTTPError: HTTP status errors

Example usage:
    >>> from glyph_forge.core.client import ForgeClient
    >>> from glyph.core.workspace import create_workspace
    >>>
    >>> ws = create_workspace(use_uuid=True)
    >>> client = ForgeClient("https://api.glyphapi.ai")
    >>>
    >>> # Build schema from DOCX
    >>> schema = client.build_schema_from_docx(
    ...     ws,
    ...     docx_path="sample.docx",
    ...     save_as="my_schema"
    ... )
    >>>
    >>> # Run schema to generate DOCX
    >>> docx_url = client.run_schema(
    ...     ws,
    ...     schema=schema,
    ...     plaintext="Sample text...",
    ...     dest_name="output.docx"
    ... )
    >>>
    >>> # Intake plaintext
    >>> result = client.intake_plaintext_text(
    ...     ws,
    ...     text="Sample text...",
    ...     save_as="intake_result"
    ... )
"""

from .forge_client import ForgeClient
from .exceptions import (
    ForgeClientError,
    ForgeClientIOError,
    ForgeClientHTTPError,
)

__all__ = [
    "ForgeClient",
    "ForgeClientError",
    "ForgeClientIOError",
    "ForgeClientHTTPError",
]