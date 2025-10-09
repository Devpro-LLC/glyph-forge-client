#!/usr/bin/env python3
"""
Example: Build schema from resume template and generate filled resume.

This script demonstrates the complete workflow:
1. Create a workspace for managing artifacts
2. Build a schema from a DOCX template (resume_1.docx)
3. Run the schema with plaintext input (resume_1.txt)
4. Save outputs to examples/outputs directory
"""

import sys
import os
from pathlib import Path
from glyph_forge import ForgeClient, create_workspace, ForgeClientHTTPError

# Load API key from environment (check both GLYPH_API_KEY and GLYPH_KEY)
if not os.getenv('GLYPH_API_KEY') and os.getenv('GLYPH_KEY'):
    os.environ['GLYPH_API_KEY'] = os.getenv('GLYPH_KEY')

# Setup paths
SCRIPT_DIR = Path(__file__).parent
EXAMPLES_DIR = SCRIPT_DIR.parent
DOCX_DIR = EXAMPLES_DIR / "test_data" / "docx"
PLAINTEXT_DIR = EXAMPLES_DIR / "test_data" / "plaintext"
OUTPUTS_DIR = EXAMPLES_DIR / "outputs"

# Input files
TEMPLATE_DOCX = DOCX_DIR / "resume_1.docx"
INPUT_TEXT = PLAINTEXT_DIR / "resume_1.txt"


def main():
    """Run the complete schema build and run workflow."""

    print("=" * 60)
    print("Glyph Forge - Resume Schema Builder Example")
    print("=" * 60)

    # Step 1: Create workspace
    print("\n[1/4] Creating workspace...")
    ws = create_workspace(
        root_dir=str(OUTPUTS_DIR),
        use_uuid=False
    )
    print(f"✓ Workspace created at: {ws.root_dir}")

    # Step 2: Initialize client
    print("\n[2/4] Initializing ForgeClient...")
    client = ForgeClient(api_key="glyph_sk_live_WPqVQJ9aDJStsbmDaQGAw6YX-1qmFr4l")  # Defaults to https://dev.glyphapi.ai
    print(f"✓ Client connected to: {client.base_url}")
    print(f"  - Using API key: {client.api_key[:12]}..." if len(client.api_key) > 12 else "  - Using API key: ***")

    try:
        # Step 3: Build schema from template
        print(f"\n[3/4] Building schema from template: {TEMPLATE_DOCX.name}")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(TEMPLATE_DOCX),
            save_as="resume_schema",
            include_artifacts=True  # Get tagged DOCX and full unzipped structure
        )
        print(f"✓ Schema built and saved")
        print(f"  - Schema has {len(schema.get('fields', []))} fields")

        # Step 4: Read plaintext input
        print(f"\n[4/4] Running schema with input: {INPUT_TEXT.name}")
        with open(INPUT_TEXT, 'r') as f:
            plaintext = f.read()

        print(f"  - Input text length: {len(plaintext)} characters")

        # Run schema to generate output
        docx_path = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name="resume_output.docx"
        )
        print(f"✓ Schema executed successfully")
        print(f"  - Output saved to: {docx_path}")

        print("\n" + "=" * 60)
        print("SUCCESS! Check the outputs directory for results:")
        print(f"\nSchema & Config:")
        print(f"  - Schema: {ws.directory('output_configs')}/resume_schema.json")
        print(f"  - Artifact metadata: {ws.directory('output_configs')}/artifact_metadata.json")
        print(f"  - Run manifest: {ws.directory('output_configs')}/run_manifest.json")
        print(f"\nInput Artifacts (with tags):")
        print(f"  - Tagged DOCX: {ws.directory('input_docx')}/")
        print(f"  - Unzipped structure: {ws.directory('input_unzipped')}/")
        print(f"\nOutput:")
        print(f"  - Generated DOCX: {docx_path}")
        print("=" * 60)

    except ForgeClientHTTPError as e:
        if e.status_code == 401:
            print("\n" + "=" * 60)
            print("❌ AUTHENTICATION FAILED (401)")
            print("=" * 60)
            print(f"\nError: {e}")
            print(f"\nAPI Key being used: {client.api_key[:20]}..." if len(client.api_key) > 20 else f"\nAPI Key: {client.api_key}")
            print("\nPossible issues:")
            print("  1. API key format is incorrect (should start with 'gf_live_' or 'gf_test_')")
            print("  2. API key is invalid or expired")
            print("  3. API key doesn't have necessary permissions")
            print("\nSteps to resolve:")
            print("  1. Check your API key in the .env file")
            print("  2. Ensure format: GLYPH_API_KEY='gf_live_...' or GLYPH_KEY='gf_live_...'")
            print("  3. Contact support if issue persists")
            print("\n" + "=" * 60)
            sys.exit(1)
        else:
            raise
    finally:
        # Cleanup
        client.close()


if __name__ == "__main__":
    main()