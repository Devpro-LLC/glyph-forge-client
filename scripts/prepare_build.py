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
        # If destination already exists (files committed to repo), skip copying
        if destination.exists():
            print(f"Source not found, but destination already exists: {destination}")
            print("Using workspace files already in repository (no copy needed)")
            copied_files = list(destination.rglob("*.py"))
            print(f"Found {len(copied_files)} Python files in existing workspace")
            return True
        else:
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

    # Fix imports: glyph.core.workspace -> glyph_forge.core.workspace
    print(f"Fixing imports in copied files...")
    import_count = 0
    for py_file in copied_files:
        content = py_file.read_text(encoding='utf-8')
        new_content = content.replace(
            'from glyph.core.workspace',
            'from glyph_forge.core.workspace'
        ).replace(
            'import glyph.core.workspace',
            'import glyph_forge.core.workspace'
        )
        if new_content != content:
            py_file.write_text(new_content, encoding='utf-8')
            import_count += 1

    print(f"Fixed imports in {import_count} files")

    # Fix FilesystemWorkspace to call parent __init__ properly
    fs_py = destination / "storage" / "fs.py"
    if fs_py.exists():
        print(f"Patching FilesystemWorkspace in storage/fs.py...")
        content = fs_py.read_text(encoding='utf-8')

        # Find and replace the __init__ method
        old_init = '''        os.makedirs(root_dir, exist_ok=True)
        self.base_root = root_dir

        # run id
        self.run_id = (
            datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
            if use_uuid else "default"
        )

        self.root_dir = os.path.join(self.base_root, self.run_id)
        os.makedirs(self.root_dir, exist_ok=True)

        self.paths = {
            "input_docx":      os.path.join(self.root_dir, "input", "docx"),
            "input_plaintext": os.path.join(self.root_dir, "input", "plaintext"),
            "input_unzipped":  os.path.join(self.root_dir, "input", "unzipped"),
            "output_configs":  os.path.join(self.root_dir, "output", "configs"),
            "output_docx":     os.path.join(self.root_dir, "output", "docx"),
        }
        if custom_paths:
            self.paths.update(custom_paths)

        for path in self.paths.values():
            # Make dirs only (skip files)
            if os.path.splitext(path)[1] == "":
                os.makedirs(path, exist_ok=True)'''

        new_init = '''        os.makedirs(root_dir, exist_ok=True)
        base_root = root_dir

        # run id
        run_id = (
            datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + str(uuid.uuid4())[:8]
            if use_uuid else "default"
        )

        root_dir_path = os.path.join(base_root, run_id)
        os.makedirs(root_dir_path, exist_ok=True)

        paths = {
            "input_docx":      os.path.join(root_dir_path, "input", "docx"),
            "input_plaintext": os.path.join(root_dir_path, "input", "plaintext"),
            "input_unzipped":  os.path.join(root_dir_path, "input", "unzipped"),
            "output_configs":  os.path.join(root_dir_path, "output", "configs"),
            "output_docx":     os.path.join(root_dir_path, "output", "docx"),
        }
        if custom_paths:
            paths.update(custom_paths)

        # Initialize parent class with all required parameters
        super().__init__(
            base_root=base_root,
            root_dir=root_dir_path,
            run_id=run_id,
            paths=paths,
        )

        # Create directories
        for path in self._paths.values():
            # Make dirs only (skip files)
            if os.path.splitext(path)[1] == "":
                os.makedirs(path, exist_ok=True)'''

        # Fix method signatures to use self._paths
        content = content.replace(old_init, new_init)
        content = content.replace('os.path.join(self.paths[key]', 'os.path.join(self._paths[key]')
        content = content.replace('for path in self.paths.values():', 'for path in self._paths.values():')
        content = content.replace('def directory(self, key: str) -> str:\n        return self.paths[key]', '')

        fs_py.write_text(content, encoding='utf-8')
        print(f"✓ Patched FilesystemWorkspace")

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