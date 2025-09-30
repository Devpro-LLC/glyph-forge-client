"""Custom Hatchling build hook for glyph-forge-client.

This hook runs the prepare_build script before building the package to ensure
workspace files from the submodule are copied into the package.
"""

import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Custom build hook to prepare workspace files."""

    def initialize(self, version, build_data):
        """Run before the build starts."""
        print("\n" + "=" * 60)
        print("Running custom build hook: prepare_build")
        print("=" * 60 + "\n")

        # Run the prepare_build script
        script_path = Path(self.root) / "scripts" / "prepare_build.py"

        if not script_path.exists():
            print(f"ERROR: Build script not found: {script_path}", file=sys.stderr)
            sys.exit(1)

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=self.root,
            capture_output=False,
        )

        if result.returncode != 0:
            print("\nERROR: Build preparation failed!", file=sys.stderr)
            sys.exit(1)

        print("\nBuild hook completed successfully\n")