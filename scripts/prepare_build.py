#!/usr/bin/env python3
"""
Build preparation script for glyph-forge-client.

This script copies specific modules from the workspace submodule into the
src/glyph_forge package structure before building. This allows us to:
1. Track workspace code in the glyph-sdk repository
2. Only include what we need in the glyph-forge package
3. Keep the package clean without the entire submodule
"""

import shutil
import sys
from pathlib import Path


def copy_workspace_module():
    """Copy workspace module from submodule to src package."""

    # Define source and destination paths
    project_root = Path(__file__).parent.parent
    source = project_root / "sdk" / "src" / "glyph" / "core" / "workspace"
    destination = project_root / "src" / "glyph_forge" / "core" / "workspace"

    # Check if source exists
    if not source.exists():
        print(f"ERROR: Source directory not found: {source}", file=sys.stderr)
        print("Make sure the workspace submodule is initialized:", file=sys.stderr)
        print("  git submodule update --init --recursive", file=sys.stderr)
        sys.exit(1)

    # Remove existing destination if it exists
    if destination.exists():
        print(f"Removing existing destination: {destination}")
        shutil.rmtree(destination)

    # Copy the workspace module
    print(f"Copying workspace module...")
    print(f"  From: {source}")
    print(f"  To:   {destination}")
    shutil.copytree(source, destination)

    # Count copied files
    copied_files = list(destination.rglob("*.py"))
    print(f"Successfully copied {len(copied_files)} Python files")

    return True


def main():
    """Main entry point for build preparation."""
    print("=" * 60)
    print("Preparing glyph-forge build")
    print("=" * 60)

    try:
        copy_workspace_module()
        print("\nBuild preparation complete!")
        return 0
    except Exception as e:
        print(f"\nERROR: Build preparation failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())