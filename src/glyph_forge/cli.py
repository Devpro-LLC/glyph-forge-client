#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Glyph Forge CLI - Command-line interface for document processing.

Usage:
    glyph-forge build-and-run <template.docx> <input.txt> [options]
    glyph-forge build <template.docx> [options]
    glyph-forge run <schema.json> <input.txt> [options]
    glyph-forge ask <message> [options]
    glyph-forge --version
    glyph-forge --help

Commands:
    build-and-run    Complete workflow: build schema + run with input
    build            Build schema from DOCX template only
    run              Run existing schema with plaintext input
    ask              Send a message to the Glyph Agent multi-agent system

Options:
    -o, --output DIR         Output directory (default: ./glyph_workspace)
    --no-uuid                Don't use UUID in workspace directory name
    --no-artifacts           Don't retrieve tagged DOCX and unzipped files
    --api-key KEY            API key (optional, or set GLYPH_API_KEY env var)
    --base-url URL           API base URL (default: https://dev.glyphapi.ai)
    --schema-name NAME       Name for saved schema file (default: schema)
    --dest-name NAME         Name for output DOCX (default: output.docx)
    -v, --verbose            Enable verbose logging
    -h, --help               Show this help message
    --version                Show version information

Examples:
    # Complete workflow with artifacts
    glyph-forge build-and-run resume.docx resume.txt -o ./output

    # Build schema only (no API key required)
    glyph-forge build template.docx -o ./my_workspace --schema-name my_schema

    # Run existing schema (no API key required)
    glyph-forge run schema.json input.txt -o ./output --dest-name result.docx

    # Disable artifact collection for faster processing
    glyph-forge build-and-run template.docx input.txt --no-artifacts

    # Use without API key (if supported by your server)
    glyph-forge build template.docx --no-artifacts

    # Send message to Glyph Agent
    glyph-forge ask "Create a schema for a quarterly report" --api-key gf_live_...
    glyph-forge ask "Add a risks section to the schema" --user-id user123 --conversation-id conv456
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from typing import Optional

from glyph_forge import ForgeClient, create_workspace, ForgeClientHTTPError, ForgeClientError
from glyph_forge.core.client.exceptions import ForgeClientIOError

# Version info
__version__ = "0.1.0"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(message)s' if not verbose else '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def load_api_key(args_key: Optional[str]) -> Optional[str]:
    """
    Load API key from args or environment (optional).

    Priority: CLI arg > GLYPH_API_KEY > GLYPH_KEY

    Returns:
        API key if found, None otherwise
    """
    if args_key:
        return args_key

    key = os.getenv('GLYPH_API_KEY') or os.getenv('GLYPH_KEY')
    return key


def print_banner(title: str) -> None:
    """Print formatted banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success_summary(ws, docx_path: Optional[str] = None, schema_only: bool = False) -> None:
    """Print success summary with artifact locations."""
    print("\n" + "=" * 70)
    print("  SUCCESS!")
    print("=" * 70)

    print("\nWorkspace Location:")
    print(f"  {ws.root_dir}")

    print("\nSchema & Config:")
    print(f"  - Schema: {ws.directory('output_configs')}/")
    print(f"  - Artifact metadata: {ws.directory('output_configs')}/artifact_metadata.json")
    if not schema_only:
        print(f"  - Run manifest: {ws.directory('output_configs')}/run_manifest.json")

    print("\nInput Artifacts (with tags):")
    print(f"  - Tagged DOCX: {ws.directory('input_docx')}/")
    print(f"  - Unzipped structure: {ws.directory('input_unzipped')}/")

    if docx_path:
        print("\nOutput:")
        print(f"  - Generated DOCX: {docx_path}")

    print("=" * 70 + "\n")


def handle_http_error(e: ForgeClientHTTPError, client: ForgeClient) -> None:
    """Handle and format HTTP errors."""
    if e.status_code == 401:
        print("\n" + "=" * 70, file=sys.stderr)
        print("  AUTHENTICATION FAILED (401)", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        print(f"\nError: {e}", file=sys.stderr)

        if client.api_key:
            masked_key = f"{client.api_key[:20]}..." if len(client.api_key) > 20 else client.api_key
            print(f"\nAPI Key being used: {masked_key}", file=sys.stderr)

            print("\nPossible issues:", file=sys.stderr)
            print("  1. API key format is incorrect (should start with 'gf_live_' or 'gf_test_')", file=sys.stderr)
            print("  2. API key is invalid or expired", file=sys.stderr)
            print("  3. API key doesn't have necessary permissions", file=sys.stderr)
        else:
            print("\nNo API key provided.", file=sys.stderr)
            print("This endpoint may require authentication.", file=sys.stderr)

        print("\nSteps to resolve:", file=sys.stderr)
        print("  1. Check your API key", file=sys.stderr)
        print("  2. Ensure format: GLYPH_API_KEY='gf_live_...' or GLYPH_KEY='gf_live_...'", file=sys.stderr)
        print("  3. Contact support if issue persists", file=sys.stderr)
        print("=" * 70 + "\n", file=sys.stderr)
        sys.exit(1)

    elif e.status_code == 403:
        print(f"\nERROR: Forbidden (403) - {e}", file=sys.stderr)
        print("Your account may be inactive or you don't have necessary permissions.\n", file=sys.stderr)
        sys.exit(1)

    elif e.status_code == 429:
        print(f"\nERROR: Rate limit exceeded (429) - {e}", file=sys.stderr)
        print("Please wait and try again later.\n", file=sys.stderr)
        sys.exit(1)

    else:
        print(f"\nHTTP ERROR ({e.status_code}): {e}\n", file=sys.stderr)
        sys.exit(1)


def cmd_build_and_run(args: argparse.Namespace) -> None:
    """Execute build-and-run command."""
    print_banner("Glyph Forge - Build & Run")

    # Validate input files
    template_path = Path(args.template).resolve()
    input_path = Path(args.input).resolve()

    if not template_path.exists():
        print(f"ERROR: Template DOCX not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load API key (optional)
    api_key = load_api_key(args.api_key)

    # Step 1: Create workspace
    print("\n[1/4] Creating workspace...")
    ws = create_workspace(
        root_dir=args.output,
        use_uuid=not args.no_uuid
    )
    print(f"Workspace created: {ws.root_dir}")

    # Step 2: Initialize client
    print("\n[2/4] Initializing ForgeClient...")
    auth_note = " (with authentication)" if api_key else " (no authentication)"
    print(f"Initializing client{auth_note}...")
    client = ForgeClient(
        api_key=api_key,
        base_url=args.base_url
    )
    print(f"Connected to: {client.base_url}")

    try:
        # Step 3: Build schema
        print(f"\n[3/4] Building schema from: {template_path.name}")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(template_path),
            save_as=args.schema_name,
            include_artifacts=not args.no_artifacts
        )
        print(f"Schema built and saved")
        print(f"  - Fields: {len(schema.get('fields', []))}")
        print(f"  - Pattern descriptors: {len(schema.get('pattern_descriptors', []))}")

        # Step 4: Run schema
        print(f"\n[4/4] Running schema with input: {input_path.name}")
        with open(input_path, 'r', encoding='utf-8') as f:
            plaintext = f.read()

        print(f"  - Input length: {len(plaintext)} characters")

        docx_path = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name=args.dest_name
        )
        print(f"Schema executed successfully")

        print_success_summary(ws, docx_path)

    except ForgeClientHTTPError as e:
        handle_http_error(e, client)
    except (ForgeClientError, ForgeClientIOError) as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


def cmd_build(args: argparse.Namespace) -> None:
    """Execute build-only command."""
    print_banner("Glyph Forge - Build Schema")

    # Validate input file
    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"ERROR: Template DOCX not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    # Load API key (optional)
    api_key = load_api_key(args.api_key)

    # Step 1: Create workspace
    print("\n[1/2] Creating workspace...")
    ws = create_workspace(
        root_dir=args.output,
        use_uuid=not args.no_uuid
    )
    print(f"Workspace created: {ws.root_dir}")

    # Step 2: Initialize client and build schema
    print("\n[2/2] Building schema...")
    auth_note = " (with authentication)" if api_key else " (no authentication)"
    print(f"Initializing client{auth_note}...")
    client = ForgeClient(
        api_key=api_key,
        base_url=args.base_url
    )
    print(f"Connected to: {client.base_url}")

    try:
        print(f"  - Processing: {template_path.name}")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(template_path),
            save_as=args.schema_name,
            include_artifacts=not args.no_artifacts
        )
        print(f"Schema built successfully")
        print(f"  - Fields: {len(schema.get('fields', []))}")
        print(f"  - Pattern descriptors: {len(schema.get('pattern_descriptors', []))}")

        print_success_summary(ws, schema_only=True)

    except ForgeClientHTTPError as e:
        handle_http_error(e, client)
    except (ForgeClientError, ForgeClientIOError) as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


def cmd_run(args: argparse.Namespace) -> None:
    """Execute run-only command."""
    print_banner("Glyph Forge - Run Schema")

    # Validate input files
    schema_path = Path(args.schema).resolve()
    input_path = Path(args.input).resolve()

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Load API key (optional)
    api_key = load_api_key(args.api_key)

    # Step 1: Create workspace
    print("\n[1/3] Creating workspace...")
    ws = create_workspace(
        root_dir=args.output,
        use_uuid=not args.no_uuid
    )
    print(f"Workspace created: {ws.root_dir}")

    # Step 2: Load schema
    print("\n[2/3] Loading schema...")
    import json
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        print(f"Schema loaded from: {schema_path.name}")
        print(f"  - Fields: {len(schema.get('fields', []))}")
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in schema file: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 3: Initialize client and run schema
    print("\n[3/3] Running schema...")
    auth_note = " (with authentication)" if api_key else " (no authentication)"
    print(f"Initializing client{auth_note}...")
    client = ForgeClient(
        api_key=api_key,
        base_url=args.base_url
    )
    print(f"Connected to: {client.base_url}")

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            plaintext = f.read()

        print(f"  - Input: {input_path.name} ({len(plaintext)} characters)")

        docx_path = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name=args.dest_name
        )
        print(f"Schema executed successfully")

        print("\n" + "=" * 70)
        print("  SUCCESS!")
        print("=" * 70)
        print(f"\nOutput:")
        print(f"  - Generated DOCX: {docx_path}")
        print("=" * 70 + "\n")

    except ForgeClientHTTPError as e:
        handle_http_error(e, client)
    except (ForgeClientError, ForgeClientIOError) as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


def cmd_ask(args: argparse.Namespace) -> None:
    """Execute ask command - send message to Glyph Agent."""
    print_banner("Glyph Forge - Ask Agent")

    # Load API key (required for ask command)
    api_key = load_api_key(args.api_key)
    if not api_key:
        print("ERROR: API key required for /ask endpoint.", file=sys.stderr)
        print("Provide --api-key or set GLYPH_API_KEY environment variable.\n", file=sys.stderr)
        sys.exit(1)

    # Initialize client
    print("\n[1/2] Initializing ForgeClient...")
    client = ForgeClient(
        api_key=api_key,
        base_url=args.base_url
    )
    print(f"Connected to: {client.base_url}")

    try:
        # Send message to agent
        print(f"\n[2/2] Sending message to agent...")
        print(f"  - Message: {args.message[:100]}{'...' if len(args.message) > 100 else ''}")
        if args.user_id:
            print(f"  - User ID: {args.user_id}")
        if args.conversation_id:
            print(f"  - Conversation ID: {args.conversation_id}")

        # Build conversation history if provided
        conversation_history = None
        if args.history_file:
            history_path = Path(args.history_file).resolve()
            if not history_path.exists():
                print(f"ERROR: History file not found: {history_path}", file=sys.stderr)
                sys.exit(1)
            import json
            with open(history_path, 'r', encoding='utf-8') as f:
                conversation_history = json.load(f)
            print(f"  - Loaded conversation history: {len(conversation_history)} messages")

        response = client.ask(
            message=args.message,
            tenant_id=args.tenant_id,
            user_id=args.user_id,
            conversation_id=args.conversation_id,
            conversation_history=conversation_history,
            real_time=args.real_time,
            strict_validation=args.strict_validation
        )

        # Print response
        print("\n" + "=" * 70)
        print("  AGENT RESPONSE")
        print("=" * 70)
        print(f"\n{response.get('response', '')}\n")

        # Show metadata
        if args.verbose:
            print("\n" + "-" * 70)
            print("  METADATA")
            print("-" * 70)
            metadata = response.get('metadata', {})
            for key, value in metadata.items():
                print(f"  - {key}: {value}")

        # Show usage
        usage = response.get('usage')
        if usage:
            print("\n" + "-" * 70)
            print("  TOKEN USAGE")
            print("-" * 70)
            print(f"  - Prompt tokens: {usage.get('prompt_tokens', 0):,}")
            print(f"  - Completion tokens: {usage.get('completion_tokens', 0):,}")
            print(f"  - Total tokens: {usage.get('total_tokens', 0):,}")

        # Show schema if present
        schema = response.get('schema') or response.get('document_schema')
        if schema:
            print("\n" + "-" * 70)
            print("  SCHEMA GENERATED")
            print("-" * 70)
            print(f"  - Pattern descriptors: {len(schema.get('pattern_descriptors', []))}")
            if args.save_schema:
                import json
                schema_path = Path(args.save_schema).resolve()
                schema_path.parent.mkdir(parents=True, exist_ok=True)
                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2)
                print(f"  - Saved to: {schema_path}")

        # Show plaintext if present
        plaintext = response.get('plaintext')
        if plaintext:
            print("\n" + "-" * 70)
            print("  PLAINTEXT GENERATED")
            print("-" * 70)
            print(f"  - Length: {len(plaintext)} characters")
            if args.save_plaintext:
                plaintext_path = Path(args.save_plaintext).resolve()
                plaintext_path.parent.mkdir(parents=True, exist_ok=True)
                with open(plaintext_path, 'w', encoding='utf-8') as f:
                    f.write(plaintext)
                print(f"  - Saved to: {plaintext_path}")

        # Show validation result if present
        validation = response.get('validation_result')
        if validation:
            print("\n" + "-" * 70)
            print("  VALIDATION RESULT")
            print("-" * 70)
            is_valid = validation.get('is_valid', False)
            print(f"  - Valid: {is_valid}")
            if not is_valid:
                errors = validation.get('errors', [])
                print(f"  - Errors: {len(errors)}")
                if args.verbose and errors:
                    for i, error in enumerate(errors[:5], 1):
                        print(f"    {i}. {error}")

        print("\n" + "=" * 70 + "\n")

    except ForgeClientHTTPError as e:
        handle_http_error(e, client)
    except (ForgeClientError, ForgeClientIOError) as e:
        print(f"\nERROR: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}\n", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='glyph-forge',
        description='Glyph Forge - Document processing with cloud-powered schema building',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Common arguments for all commands
    common_args = argparse.ArgumentParser(add_help=False)
    common_args.add_argument(
        '-o', '--output',
        default='./glyph_workspace',
        help='Output directory (default: ./glyph_workspace)'
    )
    common_args.add_argument(
        '--no-uuid',
        action='store_true',
        help="Don't use UUID in workspace directory name"
    )
    common_args.add_argument(
        '--api-key',
        help='API key (optional, or set GLYPH_API_KEY env var)'
    )
    common_args.add_argument(
        '--base-url',
        default='https://dev.glyphapi.ai',
        help='API base URL (default: https://dev.glyphapi.ai)'
    )
    common_args.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    # build-and-run command
    parser_build_run = subparsers.add_parser(
        'build-and-run',
        parents=[common_args],
        help='Build schema and run with input (complete workflow)'
    )
    parser_build_run.add_argument('template', help='Path to template DOCX file')
    parser_build_run.add_argument('input', help='Path to plaintext input file')
    parser_build_run.add_argument(
        '--no-artifacts',
        action='store_true',
        help="Don't retrieve tagged DOCX and unzipped files (faster)"
    )
    parser_build_run.add_argument(
        '--schema-name',
        default='schema',
        help='Name for saved schema file (default: schema)'
    )
    parser_build_run.add_argument(
        '--dest-name',
        default='output.docx',
        help='Name for output DOCX (default: output.docx)'
    )

    # build command
    parser_build = subparsers.add_parser(
        'build',
        parents=[common_args],
        help='Build schema from DOCX template only'
    )
    parser_build.add_argument('template', help='Path to template DOCX file')
    parser_build.add_argument(
        '--no-artifacts',
        action='store_true',
        help="Don't retrieve tagged DOCX and unzipped files (faster)"
    )
    parser_build.add_argument(
        '--schema-name',
        default='schema',
        help='Name for saved schema file (default: schema)'
    )

    # run command
    parser_run = subparsers.add_parser(
        'run',
        parents=[common_args],
        help='Run existing schema with plaintext input'
    )
    parser_run.add_argument('schema', help='Path to schema JSON file')
    parser_run.add_argument('input', help='Path to plaintext input file')
    parser_run.add_argument(
        '--dest-name',
        default='output.docx',
        help='Name for output DOCX (default: output.docx)'
    )

    # ask command
    parser_ask = subparsers.add_parser(
        'ask',
        parents=[common_args],
        help='Send a message to the Glyph Agent multi-agent system'
    )
    parser_ask.add_argument('message', help='Message to send to the agent')
    parser_ask.add_argument(
        '--user-id',
        help='User identifier for rate limiting and tracking'
    )
    parser_ask.add_argument(
        '--tenant-id',
        help='Tenant identifier for rate limiting'
    )
    parser_ask.add_argument(
        '--conversation-id',
        help='Conversation ID for context tracking'
    )
    parser_ask.add_argument(
        '--history-file',
        help='Path to JSON file with conversation history (list of {role, content} dicts)'
    )
    parser_ask.add_argument(
        '--real-time',
        action='store_true',
        help='Enable real-time sandbox updates'
    )
    parser_ask.add_argument(
        '--strict-validation',
        action='store_true',
        help='Enable strict validation mode'
    )
    parser_ask.add_argument(
        '--save-schema',
        help='Save generated schema to file (JSON)'
    )
    parser_ask.add_argument(
        '--save-plaintext',
        help='Save generated plaintext to file'
    )

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Setup logging
    setup_logging(args.verbose)

    # Route to appropriate command handler
    if args.command == 'build-and-run':
        cmd_build_and_run(args)
    elif args.command == 'build':
        cmd_build(args)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'ask':
        cmd_ask(args)


if __name__ == '__main__':
    main()
