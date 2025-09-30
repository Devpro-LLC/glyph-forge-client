#!/usr/bin/env python3
"""
End-to-end unit tests for glyph_forge client.

Tests the full workflow:
1. Workspace creation
2. ForgeClient initialization
3. Schema building from DOCX
4. Schema running with plaintext
5. Plaintext intake (text and file)
6. Error handling
7. Cleanup
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from glyph_forge import (
    ForgeClient,
    create_workspace,
    ForgeClientError,
    ForgeClientHTTPError,
    ForgeClientIOError,
)


class TestWorkspaceIntegration:
    """Test workspace creation and management."""

    def test_workspace_creation_with_uuid(self):
        """Test that workspace is created with UUID run_id."""
        ws = create_workspace(use_uuid=True)

        assert ws.run_id != "default"
        assert "_" in ws.run_id  # Should have timestamp_uuid format
        assert ws.base_root is not None
        assert ws.root_dir is not None
        assert ws.base_root in ws.root_dir

        # Verify paths exist
        assert Path(ws.root_dir).exists()
        assert Path(ws.directory("output_configs")).exists()
        assert Path(ws.directory("output_docx")).exists()

        # Cleanup
        ws.delete_workspace()

    def test_workspace_creation_default(self):
        """Test workspace creation with default run_id."""
        ws = create_workspace(use_uuid=False)

        assert ws.run_id == "default"
        assert ws.root_dir.endswith("default")

        # Cleanup
        ws.delete_workspace()

    def test_workspace_save_and_load_json(self):
        """Test saving and loading JSON artifacts."""
        ws = create_workspace(use_uuid=True)

        test_data = {
            "schema": "test",
            "version": "1.0",
            "blocks": [{"id": 1, "type": "paragraph"}]
        }

        # Save JSON
        saved_path = ws.save_json("output_configs", "test_schema", test_data)
        assert Path(saved_path).exists()
        assert saved_path.endswith("test_schema.json")

        # Load JSON
        loaded_data = ws.load_json("output_configs", "test_schema")
        assert loaded_data == test_data

        # Cleanup
        ws.delete_workspace()


class TestForgeClientInitialization:
    """Test ForgeClient initialization and configuration."""

    def test_client_with_explicit_url(self):
        """Test client initialization with explicit base URL."""
        client = ForgeClient("https://custom.api.com")
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 30.0

    def test_client_with_default_url(self):
        """Test client uses default URL when none provided."""
        client = ForgeClient()
        assert client.base_url == "https://api.glyphapi.ai"

    def test_client_with_env_variable(self):
        """Test client uses GLYPH_API_BASE environment variable."""
        with patch.dict(os.environ, {"GLYPH_API_BASE": "https://staging.api.com"}):
            client = ForgeClient()
            assert client.base_url == "https://staging.api.com"

    def test_client_strips_trailing_slash(self):
        """Test that trailing slashes are removed from base URL."""
        client = ForgeClient("https://api.example.com/")
        assert client.base_url == "https://api.example.com"

    def test_client_custom_timeout(self):
        """Test custom timeout configuration."""
        client = ForgeClient(timeout=60.0)
        assert client.timeout == 60.0

    def test_client_context_manager(self):
        """Test client can be used as context manager."""
        with ForgeClient() as client:
            assert client is not None
            assert hasattr(client, "close")


class TestBuildSchemaFromDocx:
    """Test schema building from DOCX files."""

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_build_schema_success(self, mock_client_class):
        """Test successful schema building."""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "schema": {
                "version": "1.0",
                "blocks": [{"id": 1, "type": "heading"}]
            }
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Create workspace and client
        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        # Test build_schema_from_docx
        schema = client.build_schema_from_docx(
            ws,
            docx_path="/path/to/sample.docx",
            save_as="test_schema"
        )

        assert schema is not None
        assert "version" in schema
        assert "blocks" in schema

        # Verify API call was made
        mock_client.request.assert_called_once()
        call_args = mock_client.request.call_args
        assert call_args[1]["method"] == "POST"
        assert "/schema/build" in call_args[1]["url"]

        # Verify schema was saved
        saved_schema = ws.load_json("output_configs", "test_schema")
        assert saved_schema == schema

        # Cleanup
        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_build_schema_without_save(self, mock_client_class):
        """Test schema building without saving to workspace."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"schema": {"version": "1.0"}}

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        schema = client.build_schema_from_docx(ws, docx_path="/path/to/sample.docx")

        assert schema is not None

        # Verify schema was NOT saved (no save_as parameter)
        configs_dir = Path(ws.directory("output_configs"))
        json_files = list(configs_dir.glob("*.json"))
        assert len(json_files) == 0

        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_build_schema_http_error(self, mock_client_class):
        """Test schema building with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid DOCX file"

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientHTTPError) as exc_info:
            client.build_schema_from_docx(ws, docx_path="/invalid/path.docx")

        assert exc_info.value.status_code == 400
        assert "Invalid DOCX file" in exc_info.value.response_body

        ws.delete_workspace()


class TestRunSchema:
    """Test schema running to generate DOCX."""

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_run_schema_success(self, mock_client_class):
        """Test successful schema run."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "success",
            "docx_url": "/tmp/output_20250930.docx"
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        schema = {"version": "1.0", "blocks": []}
        plaintext = "Sample text content"

        docx_url = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name="output.docx"
        )

        assert docx_url == "/tmp/output_20250930.docx"

        # Verify manifest was saved
        manifest = ws.load_json("output_configs", "run_manifest")
        assert manifest["docx_url"] == docx_url
        assert manifest["status"] == "success"
        assert manifest["dest_name"] == "output.docx"
        assert manifest["plaintext_length"] == len(plaintext)
        assert "timestamp" in manifest
        assert "schema_hash" in manifest

        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_run_schema_failure(self, mock_client_class):
        """Test schema run failure."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "failed",
            "error": "Invalid schema structure"
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientError) as exc_info:
            client.run_schema(
                ws,
                schema={},
                plaintext="test"
            )

        assert "failed" in str(exc_info.value).lower()

        ws.delete_workspace()


class TestPlaintextIntake:
    """Test plaintext intake functionality."""

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_intake_plaintext_text_success(self, mock_client_class):
        """Test plaintext intake via JSON body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "normalized_text": "Sample normalized text",
            "byte_count": 100,
            "line_count": 5,
            "stored_plaintext_path": "/tmp/intake_12345.txt"
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        result = client.intake_plaintext_text(
            ws,
            text="Sample text",
            save_as="intake_result",
            unicode_form="NFC"
        )

        assert result["normalized_text"] == "Sample normalized text"
        assert result["byte_count"] == 100

        # Verify result was saved
        saved_result = ws.load_json("output_configs", "intake_result")
        assert saved_result == result

        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_intake_plaintext_file_success(self, mock_client_class):
        """Test plaintext intake via file upload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "normalized_text": "File content",
            "byte_count": 50,
            "line_count": 3
        }

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            result = client.intake_plaintext_file(
                ws,
                file_path=temp_path,
                save_as="file_intake_result"
            )

            assert result["normalized_text"] == "File content"

            # Verify API call used multipart
            mock_client.request.assert_called_once()
            call_args = mock_client.request.call_args
            assert "files" in call_args[1]

        finally:
            os.unlink(temp_path)
            ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_intake_plaintext_file_not_found(self, mock_client_class):
        """Test plaintext intake with non-existent file."""
        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientError) as exc_info:
            client.intake_plaintext_file(
                ws,
                file_path="/nonexistent/file.txt"
            )

        assert "not found" in str(exc_info.value).lower()

        ws.delete_workspace()


class TestErrorHandling:
    """Test error handling and exception raising."""

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_network_timeout_error(self, mock_client_class):
        """Test network timeout raises ForgeClientIOError."""
        import httpx

        mock_client = Mock()
        mock_client.request.side_effect = httpx.TimeoutException("Request timeout")
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientIOError) as exc_info:
            client.build_schema_from_docx(ws, docx_path="/path/to/file.docx")

        assert "timeout" in str(exc_info.value).lower()
        assert exc_info.value.endpoint == "/schema/build"

        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_network_error(self, mock_client_class):
        """Test network error raises ForgeClientIOError."""
        import httpx

        mock_client = Mock()
        mock_client.request.side_effect = httpx.NetworkError("Connection failed")
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientIOError) as exc_info:
            client.run_schema(ws, schema={}, plaintext="test")

        assert "network" in str(exc_info.value).lower()

        ws.delete_workspace()

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_invalid_json_response(self, mock_client_class):
        """Test invalid JSON response raises ForgeClientError."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Not JSON"

        mock_client = Mock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        with pytest.raises(ForgeClientError) as exc_info:
            client.build_schema_from_docx(ws, docx_path="/path/to/file.docx")

        assert "invalid json" in str(exc_info.value).lower()

        ws.delete_workspace()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow."""

    @patch("glyph_forge.core.client.forge_client.httpx.Client")
    def test_complete_workflow(self, mock_client_class):
        """Test full workflow: intake -> build -> run."""
        # Setup mocks for all three API calls
        def mock_request(method, url, **kwargs):
            response = Mock()
            response.status_code = 200

            if "/plaintext/intake" in url:
                response.json.return_value = {
                    "normalized_text": "Normalized sample text",
                    "byte_count": 100,
                    "line_count": 5
                }
            elif "/schema/build" in url:
                response.json.return_value = {
                    "schema": {
                        "version": "1.0",
                        "blocks": [
                            {"id": 1, "type": "heading", "text": "Title"},
                            {"id": 2, "type": "paragraph", "text": "Content"}
                        ]
                    }
                }
            elif "/schema/run" in url:
                response.json.return_value = {
                    "status": "success",
                    "docx_url": "/tmp/final_output.docx"
                }

            return response

        mock_client = Mock()
        mock_client.request.side_effect = mock_request
        mock_client_class.return_value = mock_client

        # Execute workflow
        ws = create_workspace(use_uuid=True)
        client = ForgeClient()

        # Step 1: Intake plaintext
        intake_result = client.intake_plaintext_text(
            ws,
            text="Sample text for processing",
            save_as="intake"
        )
        assert intake_result["normalized_text"] == "Normalized sample text"

        # Step 2: Build schema from DOCX
        schema = client.build_schema_from_docx(
            ws,
            docx_path="/path/to/template.docx",
            save_as="schema"
        )
        assert schema["version"] == "1.0"
        assert len(schema["blocks"]) == 2

        # Step 3: Run schema with plaintext
        docx_url = client.run_schema(
            ws,
            schema=schema,
            plaintext=intake_result["normalized_text"],
            dest_name="final_output.docx"
        )
        assert docx_url == "/tmp/final_output.docx"

        # Verify all artifacts were saved
        assert Path(ws.directory("output_configs")).exists()
        saved_intake = ws.load_json("output_configs", "intake")
        saved_schema = ws.load_json("output_configs", "schema")
        manifest = ws.load_json("output_configs", "run_manifest")

        assert saved_intake == intake_result
        assert saved_schema == schema
        assert manifest["docx_url"] == docx_url

        # Verify 3 API calls were made
        assert mock_client.request.call_count == 3

        # Cleanup
        ws.delete_workspace()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])