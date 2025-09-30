"""
Glyph Forge Client - Python client for Glyph Forge API.

Main exports:
    - ForgeClient: HTTP client for Glyph Forge API
    - create_workspace: Create a workspace for managing artifacts
    - create_engine: Create an engine (local or client mode)
    - WorkspaceConfig: Configuration for engine mode selection

Example usage:
    >>> from glyph_forge import ForgeClient, create_workspace
    >>>
    >>> # Create workspace
    >>> ws = create_workspace(use_uuid=True)
    >>>
    >>> # Create client (uses default API URL)
    >>> client = ForgeClient()
    >>>
    >>> # Build schema
    >>> schema = client.build_schema_from_docx(ws, docx_path="sample.docx")
    >>>
    >>> # Run schema
    >>> docx_url = client.run_schema(ws, schema=schema, plaintext="...")
"""

__version__ = "0.1.0"

# Re-export workspace functionality
from glyph_forge.core.workspace import (
    create_workspace,
    create_engine,
    WorkspaceConfig,
    Workspace,
)

# Re-export client functionality
from glyph_forge.core.client import (
    ForgeClient,
    ForgeClientError,
    ForgeClientIOError,
    ForgeClientHTTPError,
)

__all__ = [
    # Client
    "ForgeClient",
    "ForgeClientError",
    "ForgeClientIOError",
    "ForgeClientHTTPError",
    # Workspace
    "create_workspace",
    "create_engine",
    "WorkspaceConfig",
    "Workspace",
    # Version
    "__version__",
]

