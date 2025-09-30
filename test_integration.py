#!/usr/bin/env python3
"""Quick integration test to verify workspace + client imports."""

def test_imports():
    """Test that all public API imports work."""
    print("Testing imports...")

    # Test workspace imports
    from glyph_forge import create_workspace, create_engine, WorkspaceConfig, Workspace
    print("✓ Workspace imports successful")

    # Test client imports
    from glyph_forge import ForgeClient, ForgeClientError, ForgeClientIOError, ForgeClientHTTPError
    print("✓ Client imports successful")

    # Test workspace creation
    ws = create_workspace(use_uuid=True)
    print(f"✓ Workspace created: {ws.run_id}")
    print(f"  - base_root: {ws.base_root}")
    print(f"  - root_dir: {ws.root_dir}")

    # Test client creation
    client = ForgeClient()
    print(f"✓ ForgeClient created: {client.base_url}")

    # Verify workspace has required methods
    assert hasattr(ws, 'save_json'), "Workspace missing save_json method"
    assert hasattr(ws, 'directory'), "Workspace missing directory method"
    print("✓ Workspace has required methods")

    # Verify client has required methods
    assert hasattr(client, 'build_schema_from_docx'), "Client missing build_schema_from_docx"
    assert hasattr(client, 'run_schema'), "Client missing run_schema"
    assert hasattr(client, 'intake_plaintext_text'), "Client missing intake_plaintext_text"
    assert hasattr(client, 'intake_plaintext_file'), "Client missing intake_plaintext_file"
    print("✓ Client has all required methods")

    print("\n✅ All integration tests passed!")

    # Cleanup
    ws.delete_workspace()
    print("✓ Cleanup complete")

if __name__ == "__main__":
    test_imports()