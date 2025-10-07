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
from pathlib import Path
from glyph_forge import ForgeClient, create_workspace, ForgeClientHTTPError

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
    client = ForgeClient()  # Defaults to https://dev.glyphapi.ai
    print(f"✓ Client connected to: {client.base_url}")

    try:
        # Step 3: Build schema from template
        print(f"\n[3/4] Building schema from template: {TEMPLATE_DOCX.name}")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(TEMPLATE_DOCX),
            save_as="resume_schema"
        )
        print(f"✓ Schema built and saved")
        print(f"  - Schema has {len(schema.get('fields', []))} fields")

        # Step 4: Read plaintext input
        print(f"\n[4/4] Running schema with input: {INPUT_TEXT.name}")
        with open(INPUT_TEXT, 'r') as f:
            plaintext = f.read()

        print(f"  - Input text length: {len(plaintext)} characters")

        # Run schema to generate output
        docx_url = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name="resume_output.docx"
        )
        print(f"✓ Schema executed successfully")
        print(f"  - Output location: {docx_url}")

        print("\n" + "=" * 60)
        print("SUCCESS! Check the outputs directory for results:")
        print(f"  - Schema: {ws.directory('output_configs')}/resume_schema.json")
        print(f"  - Manifest: {ws.directory('output_configs')}/run_manifest.json")
        print(f"  - Output DOCX: {docx_url}")
        print("=" * 60)

    except ForgeClientHTTPError as e:
        if e.status_code == 401:
            print("\n" + "=" * 60)
            print("❌ AUTHENTICATION REQUIRED")
            print("=" * 60)
            print("\nTo use the Glyph Forge API, you need an API key.")
            print("\nSteps to get started:")
            print("  1. Visit https://glyphapi.ai")
            print("  2. Create a free account")
            print("  3. Generate your API key")
            print("  4. Set the environment variable:")
            print("     export GLYPH_API_KEY='your-api-key-here'")
            print("\n" + "=" * 60)
            sys.exit(1)
        else:
            raise
    finally:
        # Cleanup
        client.close()


if __name__ == "__main__":
    main()