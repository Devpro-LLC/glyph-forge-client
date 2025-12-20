# Git Submodule Setup - Glyph SDK

## Overview
The Glyph SDK is integrated as a git submodule, allowing easy updates from the upstream repository while keeping the SDK code separate from the client code.

## Submodule Configuration

### Location
```
glyph-forge-client/
├── sdk/                    # Git submodule → https://github.com/Devpro-LLC/glyph-sdk.git
│   └── src/glyph/          # SDK source code
└── src/glyph_forge/        # Client source code
```

### Git Configuration
```ini
[submodule "sdk"]
    path = sdk
    url = https://github.com/Devpro-LLC/glyph-sdk.git
    branch = dev
```

## For Users (Installing from PyPI)

When users install via `pip install glyph-forge`, both the client and SDK code are included in the package. No special setup needed!

The package build process automatically includes the SDK source:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/glyph_forge", "sdk/src/glyph"]
```

## For Developers (Working with the Repository)

### Initial Clone
When cloning the repository for the first time:

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/Devpro-LLC/glyph-forge-client.git

# OR if already cloned without submodules
git submodule update --init --recursive
```

### Updating the SDK

To pull the latest changes from the SDK repository:

```bash
# Update submodule to latest commit on tracked branch (dev)
git submodule update --remote sdk

# Commit the submodule update
git add sdk
git commit -m "Update SDK submodule to latest"
git push
```

### Checking SDK Version

```bash
# See current SDK commit
cd sdk
git log -1 --oneline
cd ..

# See which branch is tracked
git config -f .gitmodules submodule.sdk.branch
```

### Switching SDK Branches

```bash
# Change tracked branch in .gitmodules
git config -f .gitmodules submodule.sdk.branch main

# Update submodule to new branch
git submodule update --remote sdk

# Commit the change
git add .gitmodules sdk
git commit -m "Switch SDK submodule to main branch"
```

### Testing Local SDK Changes

If you need to test changes to the SDK before they're merged upstream:

```bash
# Make changes in sdk/ directory
cd sdk
# ... make changes ...
git add .
git commit -m "Test changes"

# Test with client
cd ..
python -m pytest

# When done testing, revert to upstream
cd sdk
git reset --hard origin/dev
cd ..
```

## Project Structure

### Import Paths

**SDK Code (from submodule):**
```python
from glyph.core.schema.build_schema import GlyphSchemaBuilder
from glyph.core.schema_runner.run_schema import GlyphSchemaRunner
from glyph.core.utils.docx_intake import intake_docx
from glyph.core.workspace import Workspace
```

**Client Code:**
```python
from glyph_forge.core.client import ForgeClient
from glyph_forge.core.compression import compress_schema  # Local utility
from glyph_forge import create_workspace  # Wrapper around SDK Workspace
```

### Build Configuration

The `pyproject.toml` maps both source directories:

```toml
[tool.hatch.build.sources]
glyph_forge = "src/glyph_forge"
glyph = "sdk/src/glyph"
```

This allows both `glyph_forge` and `glyph` imports to work when the package is installed.

## Development Workflow

### Running Tests

```bash
# Set PYTHONPATH to include both client and SDK
export PYTHONPATH=./src:./sdk/src

# Run tests
python -m pytest

# Or use the shorthand
PYTHONPATH=./src:./sdk/src python -m pytest
```

### Building Package

```bash
# Build distributions (wheel + sdist)
python -m build

# The SDK submodule code is automatically included
ls -lh dist/
```

### Installing for Development

```bash
# Install in editable mode with SDK
pip install -e .

# Test imports
python -c "from glyph_forge import ForgeClient; from glyph.core.workspace import Workspace; print('Success!')"
```

## Benefits of Submodule Approach

✅ **Easy Updates** - Pull latest SDK changes with `git submodule update --remote`
✅ **Version Control** - Exact SDK commit is tracked in client repo
✅ **Separate Concerns** - SDK and client have independent git history
✅ **Atomic Updates** - Update SDK and client together in one commit
✅ **No Duplication** - Single source of truth for SDK code
✅ **Flexible** - Can test local SDK changes before merging upstream

## Troubleshooting

### Submodule Not Initialized

**Problem:** `sdk/` directory is empty

**Solution:**
```bash
git submodule update --init --recursive
```

### Import Errors in Development

**Problem:** `ModuleNotFoundError: No module named 'glyph'`

**Solution:**
```bash
# Ensure SDK submodule is initialized
git submodule update --init

# Add SDK to PYTHONPATH
export PYTHONPATH=./src:./sdk/src
```

### Submodule Detached HEAD

**Problem:** `sdk/` is in detached HEAD state

**Solution:**
```bash
cd sdk
git checkout dev  # or whatever branch you need
cd ..
```

### Merge Conflicts with Submodule

**Problem:** Git conflict in `.gitmodules` or `sdk` pointer

**Solution:**
```bash
# Accept their version
git checkout --theirs sdk
git add sdk

# Or accept your version
git checkout --ours sdk
git add sdk

# Then update submodule
git submodule update --init --recursive
```

## Continuous Integration

For CI/CD pipelines, ensure submodules are cloned:

```yaml
# GitHub Actions example
- uses: actions/checkout@v4
  with:
    submodules: recursive

# GitLab CI example
variables:
  GIT_SUBMODULE_STRATEGY: recursive
```

## Summary

The git submodule approach provides:
- **Clean separation** between SDK and client code
- **Easy synchronization** with upstream SDK changes
- **Transparent integration** for end users (they just `pip install`)
- **Flexible development** workflow for contributors

To update the SDK, simply run:
```bash
git submodule update --remote sdk
git add sdk
git commit -m "Update SDK submodule"
git push
```

That's it! The SDK is now ready to be used in the client.
