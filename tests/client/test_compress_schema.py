#!/usr/bin/env python3
"""
Unit tests for ForgeClient.compress_schema method.

Tests the schema compression functionality:
1. Create a schema with redundant pattern descriptors
2. Compress the schema using ForgeClient
3. Verify compression statistics and deduplicated schema
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from glyph_forge import ForgeClient, create_workspace


# Mock API key for testing
TEST_API_KEY = "gf_test_mock_key_for_compression_tests"


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_compress_schema_")
    ws = create_workspace(root_dir=temp_dir, use_uuid=False)
    yield ws
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_forge_client():
    """Create a mocked ForgeClient instance."""
    with patch('glyph_forge.core.client.forge_client.httpx.Client'):
        client = ForgeClient(api_key=TEST_API_KEY)
        yield client
        client.close()


def create_test_schema_with_duplicates():
    """
    Create a test schema with redundant pattern descriptors.

    This simulates a schema where the same pattern type (e.g., "H-SHORT")
    appears multiple times, which is common in schemas built from complex documents.
    """
    return {
        "pattern_descriptors": [
            {
                "type": "H-SHORT",
                "score": 0.85,
                "style": {"font": {"bold": True, "size": 24}},
            },
            {
                "type": "H-SHORT",
                "score": 0.90,
                "style": {"font": {"bold": True, "size": 24}},
            },
            {
                "type": "PARAGRAPH",
                "score": 0.75,
                "style": {"font": {"bold": False, "size": 12}},
            },
            {
                "type": "H-SHORT",
                "score": 0.88,
                "style": {"font": {"bold": True, "size": 24}},
            },
            {
                "type": "PARAGRAPH",
                "score": 0.80,
                "style": {"font": {"bold": False, "size": 12}},
            },
        ],
        "global_defaults": {
            "page_size": {"width": 12240, "height": 15840},
            "margins": {"left": 1440, "right": 1440, "top": 1440, "bottom": 1440},
        },
        "source_docx_base64": "mock_base64_data",
    }


class TestCompressSchema:
    """Test ForgeClient.compress_schema method."""

    def test_compress_schema_success(self, temp_workspace, mock_forge_client):
        """
        Test successful schema compression.

        Verifies that:
        1. The request is made to the correct endpoint
        2. Response is properly parsed
        3. Compressed schema has fewer pattern descriptors
        4. Statistics are correctly returned
        """
        ws = temp_workspace
        client = mock_forge_client

        # Create test schema with duplicates
        test_schema = create_test_schema_with_duplicates()

        # Mock API response
        mock_response = {
            "compressed_schema": {
                "pattern_descriptors": [
                    {
                        "type": "H-SHORT",
                        "score": 0.90,
                        "style": {"font": {"bold": True, "size": 24}},
                    },
                    {
                        "type": "PARAGRAPH",
                        "score": 0.80,
                        "style": {"font": {"bold": False, "size": 12}},
                    },
                ],
                "global_defaults": test_schema["global_defaults"],
                "source_docx_base64": test_schema["source_docx_base64"],
            },
            "stats": {
                "original_count": 5,
                "compressed_count": 2,
                "reduction": 3,
                "reduction_percentage": 60.0,
                "deduplication_summary": {
                    "H-SHORT": {"original": 3, "compressed": 1},
                    "PARAGRAPH": {"original": 2, "compressed": 1},
                },
            },
        }

        # Mock the _make_request method
        client._make_request = Mock(return_value=mock_response)

        # Call compress_schema
        result = client.compress_schema(ws, schema=test_schema)

        # Verify _make_request was called correctly
        client._make_request.assert_called_once_with(
            "POST",
            "/schema/compress",
            json_data={"schema": test_schema},
        )

        # Verify response structure
        assert "compressed_schema" in result
        assert "stats" in result

        # Verify compression worked
        compressed_schema = result["compressed_schema"]
        stats = result["stats"]

        assert len(compressed_schema["pattern_descriptors"]) == 2
        assert stats["original_count"] == 5
        assert stats["compressed_count"] == 2
        assert stats["reduction"] == 3
        assert stats["reduction_percentage"] == 60.0

    def test_compress_schema_with_save_as(self, temp_workspace, mock_forge_client):
        """
        Test schema compression with save_as parameter.

        Verifies that the compressed schema is saved to workspace when save_as is provided.
        """
        ws = temp_workspace
        client = mock_forge_client

        test_schema = create_test_schema_with_duplicates()

        # Mock API response
        mock_compressed = {
            "pattern_descriptors": [
                {"type": "H-SHORT", "score": 0.90},
            ],
            "global_defaults": test_schema["global_defaults"],
        }

        mock_response = {
            "compressed_schema": mock_compressed,
            "stats": {
                "original_count": 5,
                "compressed_count": 1,
                "reduction": 4,
                "reduction_percentage": 80.0,
            },
        }

        client._make_request = Mock(return_value=mock_response)

        # Call with save_as
        result = client.compress_schema(
            ws,
            schema=test_schema,
            save_as="compressed_test_schema"
        )

        # Verify compressed schema was saved
        saved_files = list(Path(ws.directory("output_configs")).glob("*.json"))
        assert len(saved_files) > 0

        # Verify the saved file contains the compressed schema
        import json
        for file in saved_files:
            if "compressed_test_schema" in file.name:
                with open(file, 'r') as f:
                    saved_data = json.load(f)
                assert saved_data == mock_compressed
                break
        else:
            pytest.fail("Compressed schema file not found in workspace")

    def test_compress_schema_missing_response(self, temp_workspace, mock_forge_client):
        """
        Test error handling when API response is missing compressed_schema.
        """
        ws = temp_workspace
        client = mock_forge_client

        test_schema = create_test_schema_with_duplicates()

        # Mock API response without compressed_schema
        mock_response = {
            "stats": {"original_count": 5, "compressed_count": 2},
        }

        client._make_request = Mock(return_value=mock_response)

        # Should raise ForgeClientError
        from glyph_forge.core.client.exceptions import ForgeClientError

        with pytest.raises(ForgeClientError) as exc_info:
            client.compress_schema(ws, schema=test_schema)

        assert "Missing 'compressed_schema' in API response" in str(exc_info.value)

    def test_compress_schema_preserves_other_fields(self, temp_workspace, mock_forge_client):
        """
        Test that compression preserves all schema fields except pattern_descriptors.
        """
        ws = temp_workspace
        client = mock_forge_client

        test_schema = create_test_schema_with_duplicates()

        # Mock response that preserves other fields
        mock_compressed = {
            "pattern_descriptors": [{"type": "H-SHORT", "score": 0.90}],
            "global_defaults": test_schema["global_defaults"],
            "source_docx_base64": test_schema["source_docx_base64"],
        }

        mock_response = {
            "compressed_schema": mock_compressed,
            "stats": {"original_count": 5, "compressed_count": 1},
        }

        client._make_request = Mock(return_value=mock_response)

        result = client.compress_schema(ws, schema=test_schema)

        compressed = result["compressed_schema"]

        # Verify global_defaults preserved
        assert compressed["global_defaults"] == test_schema["global_defaults"]

        # Verify source_docx_base64 preserved
        assert compressed["source_docx_base64"] == test_schema["source_docx_base64"]

    def test_compress_schema_http_error(self, temp_workspace, mock_forge_client):
        """
        Test error handling for HTTP errors during compression.
        """
        ws = temp_workspace
        client = mock_forge_client

        test_schema = create_test_schema_with_duplicates()

        # Mock HTTP error
        from glyph_forge.core.client.exceptions import ForgeClientHTTPError

        client._make_request = Mock(
            side_effect=ForgeClientHTTPError(
                "HTTP 500 from /schema/compress",
                status_code=500,
                response_body="Internal server error",
                endpoint="/schema/compress",
            )
        )

        with pytest.raises(ForgeClientHTTPError) as exc_info:
            client.compress_schema(ws, schema=test_schema)

        assert exc_info.value.status_code == 500
        assert "/schema/compress" in str(exc_info.value)

    def test_compress_schema_empty_pattern_descriptors(self, temp_workspace, mock_forge_client):
        """
        Test compression with schema that has no pattern descriptors.
        """
        ws = temp_workspace
        client = mock_forge_client

        # Schema with empty pattern_descriptors
        test_schema = {
            "pattern_descriptors": [],
            "global_defaults": {"page_size": {"width": 12240, "height": 15840}},
        }

        mock_response = {
            "compressed_schema": test_schema.copy(),
            "stats": {
                "original_count": 0,
                "compressed_count": 0,
                "reduction": 0,
                "reduction_percentage": 0.0,
            },
        }

        client._make_request = Mock(return_value=mock_response)

        result = client.compress_schema(ws, schema=test_schema)

        assert result["stats"]["original_count"] == 0
        assert result["stats"]["compressed_count"] == 0
        assert result["stats"]["reduction"] == 0


if __name__ == "__main__":
    # Run with: pytest tests/client/test_compress_schema.py -v -s
    pytest.main([__file__, "-v", "-s"])
