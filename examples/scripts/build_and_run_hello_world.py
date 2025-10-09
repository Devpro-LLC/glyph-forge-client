#!/usr/bin/env python3
"""
Test script: Build schema from hello_world.docx and run with plaintext.

This script tests the styling pipeline:
1. Build schema from hello_world.docx (contains "hello world" in red/bold)
2. Run schema with plaintext from helloworld.txt
3. Outputs can be validated with tests/client/test_hello_world_styling.py
"""

import sys
import os
from pathlib import Path
from glyph_forge import ForgeClient, create_workspace, ForgeClientHTTPError

# Setup paths
SCRIPT_DIR = Path(__file__).parent
EXAMPLES_DIR = SCRIPT_DIR.parent
DOCX_DIR = EXAMPLES_DIR / "test_data" / "docx"
PLAINTEXT_DIR = EXAMPLES_DIR / "test_data" / "plaintext"
OUTPUTS_DIR = EXAMPLES_DIR / "outputs"

# Input files
TEMPLATE_DOCX = DOCX_DIR / "hello_world.docx"
INPUT_TEXT = PLAINTEXT_DIR / "helloworld.txt"

# API key
API_KEY = "glyph_sk_live_WPqVQJ9aDJStsbmDaQGAw6YX-1qmFr4l"


def main():
    """Run the hello world styling test."""

    print("=" * 60)
    print("Glyph Forge - Hello World Styling Test")
    print("=" * 60)

    # Verify input files exist
    if not TEMPLATE_DOCX.exists():
        print(f"\nERROR: Template DOCX not found: {TEMPLATE_DOCX}")
        print("Please create this file with 'hello world' text in RED and BOLD")
        sys.exit(1)

    if not INPUT_TEXT.exists():
        print(f"\nERROR: Input text file not found: {INPUT_TEXT}")
        print("Please create this file with plaintext content")
        sys.exit(1)

    # Step 1: Create workspace
    print("\n[1/4] Creating workspace...")
    ws = create_workspace(
        root_dir=str(OUTPUTS_DIR / "hello_world_test"),
        use_uuid=False
    )
    print(f"✓ Workspace created at: {ws.root_dir}")

    # Step 2: Initialize client
    print("\n[2/4] Initializing ForgeClient...")
    client = ForgeClient(api_key=API_KEY)
    print(f"✓ Client connected to: {client.base_url}")

    try:
        # Step 3: Build schema from template
        print(f"\n[3/4] Building schema from: {TEMPLATE_DOCX.name}")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(TEMPLATE_DOCX),
            save_as="hello_world_schema",
            include_artifacts=True
        )
        print(f"✓ Schema built and saved")
        print(f"  - Pattern descriptors: {len(schema.get('pattern_descriptors', []))}")

        # Print style info from first descriptor
        if schema.get('pattern_descriptors'):
            first_desc = schema['pattern_descriptors'][0]
            print(f"  - First descriptor type: {first_desc.get('type')}")
            print(f"  - First descriptor style: {first_desc.get('style', {})}")

        # Step 4: Read plaintext input
        print(f"\n[4/4] Running schema with input: {INPUT_TEXT.name}")
        with open(INPUT_TEXT, 'r') as f:
            plaintext = f.read()

        print(f"  - Input text: '{plaintext.strip()}'")

        # Run schema to generate output
        docx_path = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name="hello_world_output.docx"
        )
        print(f"✓ Schema executed successfully")
        print(f"  - Output saved to: {docx_path}")

        print("\n" + "=" * 60)
        print("SUCCESS! Files created:")
        print(f"\nOriginal Template:")
        print(f"  {TEMPLATE_DOCX}")
        print(f"\nSchema:")
        print(f"  {ws.directory('output_configs')}/hello_world_schema.json")
        print(f"\nTagged Input (with style info):")
        print(f"  {ws.directory('input_docx')}/")
        print(f"\nOutput DOCX:")
        print(f"  {docx_path}")
        print("\n" + "=" * 60)
        print("\nRun validation test:")
        print("  pytest tests/client/test_hello_world_styling.py -v")
        print("=" * 60)

    except ForgeClientHTTPError as e:
        if e.status_code == 401:
            print("\n" + "=" * 60, file=sys.stderr)
            print("❌ AUTHENTICATION FAILED (401)", file=sys.stderr)
            print("=" * 60, file=sys.stderr)
            print(f"\nError: {e}", file=sys.stderr)
            sys.exit(1)
        else:
            raise
    finally:
        client.close()


if __name__ == "__main__":
    main()
