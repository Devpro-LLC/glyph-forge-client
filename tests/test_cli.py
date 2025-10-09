"""
Unit tests for Glyph Forge CLI (src/glyph_forge/cli.py)

Tests cover:
- Argument parsing
- Command routing
- Error handling
- API key loading
- File validation
- Success/error output formatting
"""

import pytest
import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from io import StringIO

from glyph_forge.cli import (
    main,
    load_api_key,
    cmd_build_and_run,
    cmd_build,
    cmd_run,
    print_banner,
    print_success_summary,
    handle_http_error,
    setup_logging,
)
from glyph_forge import ForgeClientHTTPError


class TestLoadApiKey:
    """Test API key loading logic."""

    def test_load_from_argument(self):
        """Should prioritize CLI argument over environment."""
        with patch.dict(os.environ, {'GLYPH_API_KEY': 'env_key'}):
            result = load_api_key('arg_key')
            assert result == 'arg_key'

    def test_load_from_glyph_api_key_env(self):
        """Should load from GLYPH_API_KEY environment variable."""
        with patch.dict(os.environ, {'GLYPH_API_KEY': 'test_key'}):
            result = load_api_key(None)
            assert result == 'test_key'

    def test_load_from_glyph_key_env(self):
        """Should load from GLYPH_KEY environment variable as fallback."""
        with patch.dict(os.environ, {'GLYPH_KEY': 'fallback_key'}, clear=True):
            result = load_api_key(None)
            assert result == 'fallback_key'

    def test_glyph_api_key_takes_precedence(self):
        """GLYPH_API_KEY should take precedence over GLYPH_KEY."""
        with patch.dict(os.environ, {'GLYPH_API_KEY': 'primary', 'GLYPH_KEY': 'secondary'}):
            result = load_api_key(None)
            assert result == 'primary'

    def test_missing_api_key_exits(self, capsys):
        """Should exit with error when no API key is found."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                load_api_key(None)

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "API key not found" in captured.err


class TestPrintFunctions:
    """Test output formatting functions."""

    def test_print_banner(self, capsys):
        """Should print formatted banner."""
        print_banner("Test Title")
        captured = capsys.readouterr()
        assert "Test Title" in captured.out
        assert "=" * 70 in captured.out

    def test_print_success_summary_with_docx(self, capsys):
        """Should print complete success summary with output DOCX."""
        mock_ws = Mock()
        mock_ws.root_dir = "/test/workspace"
        mock_ws.directory.return_value = "/test/workspace/output"

        print_success_summary(mock_ws, docx_path="/test/output.docx")

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out
        assert "/test/workspace" in captured.out
        assert "output.docx" in captured.out
        assert "Schema & Config" in captured.out
        assert "Input Artifacts" in captured.out

    def test_print_success_summary_schema_only(self, capsys):
        """Should print schema-only success summary."""
        mock_ws = Mock()
        mock_ws.root_dir = "/test/workspace"
        mock_ws.directory.return_value = "/test/workspace/output"

        print_success_summary(mock_ws, schema_only=True)

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out
        assert "Run manifest" not in captured.out  # Should not show run manifest
        assert "Schema & Config" in captured.out


class TestHandleHttpError:
    """Test HTTP error handling."""

    def test_handle_401_error(self, capsys):
        """Should handle 401 authentication errors with helpful message."""
        mock_client = Mock()
        mock_client.api_key = "test_key_1234567890123456789"
        error = ForgeClientHTTPError(
            "Unauthorized",
            status_code=401,
            response_body="Invalid API key",
            endpoint="/test"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_http_error(error, mock_client)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "AUTHENTICATION FAILED" in captured.err
        assert "test_key_12345678901..." in captured.err  # Masked key (20 chars + ...)
        assert "Possible issues" in captured.err

    def test_handle_403_error(self, capsys):
        """Should handle 403 forbidden errors."""
        mock_client = Mock()
        error = ForgeClientHTTPError(
            "Forbidden",
            status_code=403,
            response_body="Account inactive",
            endpoint="/test"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_http_error(error, mock_client)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Forbidden (403)" in captured.err
        assert "inactive" in captured.err

    def test_handle_429_error(self, capsys):
        """Should handle 429 rate limit errors."""
        mock_client = Mock()
        error = ForgeClientHTTPError(
            "Rate limit exceeded",
            status_code=429,
            response_body="Too many requests",
            endpoint="/test"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_http_error(error, mock_client)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Rate limit exceeded" in captured.err

    def test_handle_generic_http_error(self, capsys):
        """Should handle generic HTTP errors."""
        mock_client = Mock()
        error = ForgeClientHTTPError(
            "Server error",
            status_code=500,
            response_body="Internal error",
            endpoint="/test"
        )

        with pytest.raises(SystemExit) as exc_info:
            handle_http_error(error, mock_client)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "HTTP ERROR (500)" in captured.err


class TestCommandBuildAndRun:
    """Test build-and-run command."""

    @patch('glyph_forge.cli.ForgeClient')
    @patch('glyph_forge.cli.create_workspace')
    @patch('glyph_forge.cli.Path')
    @patch('builtins.open', new_callable=mock_open, read_data='test plaintext content')
    def test_build_and_run_success(self, mock_file, mock_path, mock_workspace, mock_client, capsys):
        """Should execute complete build-and-run workflow successfully."""
        # Setup mocks
        mock_args = Mock()
        mock_args.template = 'template.docx'
        mock_args.input = 'input.txt'
        mock_args.output = './output'
        mock_args.no_uuid = False
        mock_args.no_artifacts = False
        mock_args.api_key = 'test_key'
        mock_args.base_url = 'https://test.api'
        mock_args.schema_name = 'test_schema'
        mock_args.dest_name = 'output.docx'
        mock_args.verbose = False

        # Mock Path.exists() to return True
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path_instance.name = 'template.docx'
        mock_path.return_value = mock_path_instance

        # Mock workspace
        mock_ws = Mock()
        mock_ws.root_dir = './output/test'
        mock_ws.directory.return_value = './output/test/configs'
        mock_workspace.return_value = mock_ws

        # Mock client
        mock_client_instance = Mock()
        mock_client_instance.base_url = 'https://test.api'
        mock_client_instance.build_schema_from_docx.return_value = {
            'fields': ['field1', 'field2'],
            'pattern_descriptors': ['desc1', 'desc2']
        }
        mock_client_instance.run_schema.return_value = './output/test/output.docx'
        mock_client.return_value = mock_client_instance

        # Execute
        cmd_build_and_run(mock_args)

        # Verify
        mock_workspace.assert_called_once()
        mock_client_instance.build_schema_from_docx.assert_called_once_with(
            mock_ws,
            docx_path=str(mock_path_instance),
            save_as='test_schema',
            include_artifacts=True
        )
        mock_client_instance.run_schema.assert_called_once()
        mock_client_instance.close.assert_called_once()

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out

    @patch('glyph_forge.cli.Path')
    def test_build_and_run_missing_template(self, mock_path, capsys):
        """Should exit with error when template file is missing."""
        mock_args = Mock()
        mock_args.template = 'missing.docx'
        mock_args.input = 'input.txt'

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path.return_value = mock_path_instance

        with pytest.raises(SystemExit) as exc_info:
            cmd_build_and_run(mock_args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Template DOCX not found" in captured.err

    @patch('glyph_forge.cli.ForgeClient')
    @patch('glyph_forge.cli.create_workspace')
    @patch('glyph_forge.cli.Path')
    def test_build_and_run_http_error(self, mock_path, mock_workspace, mock_client, capsys):
        """Should handle HTTP errors gracefully."""
        mock_args = Mock()
        mock_args.template = 'template.docx'
        mock_args.input = 'input.txt'
        mock_args.output = './output'
        mock_args.no_uuid = False
        mock_args.no_artifacts = False
        mock_args.api_key = 'test_key'
        mock_args.base_url = 'https://test.api'
        mock_args.schema_name = 'test_schema'
        mock_args.verbose = False

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path.return_value = mock_path_instance

        mock_ws = Mock()
        mock_workspace.return_value = mock_ws

        mock_client_instance = Mock()
        mock_client_instance.api_key = 'test_key_123'
        mock_client_instance.build_schema_from_docx.side_effect = ForgeClientHTTPError(
            "Unauthorized",
            status_code=401,
            response_body="Invalid key",
            endpoint="/build"
        )
        mock_client.return_value = mock_client_instance

        with pytest.raises(SystemExit) as exc_info:
            cmd_build_and_run(mock_args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "AUTHENTICATION FAILED" in captured.err


class TestCommandBuild:
    """Test build-only command."""

    @patch('glyph_forge.cli.ForgeClient')
    @patch('glyph_forge.cli.create_workspace')
    @patch('glyph_forge.cli.Path')
    def test_build_success(self, mock_path, mock_workspace, mock_client, capsys):
        """Should build schema successfully."""
        mock_args = Mock()
        mock_args.template = 'template.docx'
        mock_args.output = './output'
        mock_args.no_uuid = False
        mock_args.no_artifacts = False
        mock_args.api_key = 'test_key'
        mock_args.base_url = 'https://test.api'
        mock_args.schema_name = 'test_schema'
        mock_args.verbose = False

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path_instance.name = 'template.docx'
        mock_path.return_value = mock_path_instance

        mock_ws = Mock()
        mock_ws.root_dir = './output/test'
        mock_ws.directory.return_value = './output/test/configs'
        mock_workspace.return_value = mock_ws

        mock_client_instance = Mock()
        mock_client_instance.base_url = 'https://test.api'
        mock_client_instance.build_schema_from_docx.return_value = {
            'fields': ['field1'],
            'pattern_descriptors': ['desc1']
        }
        mock_client.return_value = mock_client_instance

        cmd_build(mock_args)

        mock_client_instance.build_schema_from_docx.assert_called_once()
        mock_client_instance.close.assert_called_once()

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out
        assert "Build Schema" in captured.out


class TestCommandRun:
    """Test run-only command."""

    @patch('glyph_forge.cli.ForgeClient')
    @patch('glyph_forge.cli.create_workspace')
    @patch('glyph_forge.cli.Path')
    @patch('builtins.open')
    def test_run_success(self, mock_open_func, mock_path, mock_workspace, mock_client, capsys):
        """Should run schema successfully."""
        mock_args = Mock()
        mock_args.schema = 'schema.json'
        mock_args.input = 'input.txt'
        mock_args.output = './output'
        mock_args.no_uuid = False
        mock_args.api_key = 'test_key'
        mock_args.base_url = 'https://test.api'
        mock_args.dest_name = 'output.docx'
        mock_args.verbose = False

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path_instance.name = 'schema.json'
        mock_path.return_value = mock_path_instance

        # Mock file reading
        schema_data = json.dumps({'fields': ['field1']})
        plaintext_data = 'test plaintext'

        mock_schema_file = MagicMock()
        mock_schema_file.__enter__.return_value.read.return_value = schema_data
        mock_plaintext_file = MagicMock()
        mock_plaintext_file.__enter__.return_value.read.return_value = plaintext_data

        mock_open_func.side_effect = [mock_schema_file, mock_plaintext_file]

        mock_ws = Mock()
        mock_workspace.return_value = mock_ws

        mock_client_instance = Mock()
        mock_client_instance.base_url = 'https://test.api'
        mock_client_instance.run_schema.return_value = './output/output.docx'
        mock_client.return_value = mock_client_instance

        cmd_run(mock_args)

        mock_client_instance.run_schema.assert_called_once()
        mock_client_instance.close.assert_called_once()

        captured = capsys.readouterr()
        assert "SUCCESS" in captured.out

    @patch('glyph_forge.cli.Path')
    @patch('builtins.open')
    def test_run_invalid_json(self, mock_open_func, mock_path, capsys):
        """Should exit with error when schema JSON is invalid."""
        mock_args = Mock()
        mock_args.schema = 'schema.json'
        mock_args.input = 'input.txt'
        mock_args.output = './output'
        mock_args.no_uuid = False
        mock_args.api_key = 'test_key'

        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.resolve.return_value = mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock invalid JSON
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "invalid json{"
        mock_open_func.return_value = mock_file

        with pytest.raises(SystemExit) as exc_info:
            cmd_run(mock_args)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Invalid JSON" in captured.err


class TestMainEntry:
    """Test main CLI entry point."""

    @patch('sys.argv', ['glyph-forge'])
    def test_main_no_command(self, capsys):
        """Should show help when no command is provided."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch('sys.argv', ['glyph-forge', '--version'])
    def test_main_version(self):
        """Should display version information."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch('sys.argv', ['glyph-forge', 'build-and-run', '--help'])
    def test_main_build_and_run_help(self):
        """Should display help for build-and-run command."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0


class TestSetupLogging:
    """Test logging configuration."""

    def test_setup_logging_normal(self):
        """Should configure INFO logging by default."""
        import logging
        setup_logging(verbose=False)
        # Just verify it doesn't crash - actual level checking is complex

    def test_setup_logging_verbose(self):
        """Should configure DEBUG logging in verbose mode."""
        import logging
        setup_logging(verbose=True)
        # Just verify it doesn't crash


# Integration-style tests with real argument parsing
class TestArgumentParsing:
    """Test argument parsing without mocking."""

    @patch('sys.argv', ['glyph-forge', 'build-and-run', 'template.docx', 'input.txt'])
    @patch('glyph_forge.cli.cmd_build_and_run')
    def test_parse_build_and_run(self, mock_cmd):
        """Should parse build-and-run arguments correctly."""
        main()

        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.template == 'template.docx'
        assert args.input == 'input.txt'
        assert args.command == 'build-and-run'

    @patch('sys.argv', ['glyph-forge', 'build', 'template.docx', '--no-artifacts'])
    @patch('glyph_forge.cli.cmd_build')
    def test_parse_build_with_flags(self, mock_cmd):
        """Should parse build command with flags."""
        main()

        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.template == 'template.docx'
        assert args.no_artifacts is True

    @patch('sys.argv', ['glyph-forge', 'run', 'schema.json', 'input.txt', '-o', './custom_output'])
    @patch('glyph_forge.cli.cmd_run')
    def test_parse_run_with_output(self, mock_cmd):
        """Should parse run command with custom output."""
        main()

        mock_cmd.assert_called_once()
        args = mock_cmd.call_args[0][0]
        assert args.schema == 'schema.json'
        assert args.input == 'input.txt'
        assert args.output == './custom_output'
