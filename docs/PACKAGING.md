# Packaging Strategy for glyph-forge-client

## Overview

This document explains how the glyph-forge-client package is built and distributed, ensuring that only necessary code is included in the pip package (no redundant SDK code).

## Directory Structure

```
glyph-forge-client/
├── src/glyph_forge/              # Main package (gets packaged)
│   ├── core/
│   │   ├── client/               # HTTP client code
│   │   ├── workspace/            # Workspace code (copied from SDK)
│   │   ├── schema/               # Schema stubs
│   │   └── plaintext/            # Plaintext stubs
│   └── __init__.py
├── sdk/                          # Git submodule (NOT packaged)
│   └── src/glyph/core/workspace/ # Source of workspace code
├── scripts/
│   └── prepare_build.py          # Build preparation script
└── hatch_build.py                # Hatchling build hook
```

## Build Process

### 1. Pre-Build Preparation (`hatch_build.py`)

The custom build hook runs **before** the package is built:

```python
# hatch_build.py triggers scripts/prepare_build.py
```

This script:
- Copies `sdk/src/glyph/core/workspace/` → `src/glyph_forge/core/workspace/`
- Updates import paths from `glyph.core.workspace` → `glyph_forge.core.workspace`
- Ensures workspace module is available during build

### 2. Wheel Build Configuration (`pyproject.toml`)

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/glyph_forge"]
artifacts = [
  "src/glyph_forge/core/workspace/**/*.py",
]
```

**Key Points:**
- `packages = ["src/glyph_forge"]` - Only package code from `src/glyph_forge/`
- `artifacts` - Force include workspace files (needed because they're created during build)
- `sdk/` directory is **never** included in the wheel

### 3. Source Distribution (sdist) Configuration

```toml
[tool.hatch.build.targets.sdist]
include = [
    "src/glyph_forge",
    "scripts/prepare_build.py",
    "hatch_build.py",
    "README.md",
    "LICENSE",
    "pyproject.toml",
    "sdk/src/glyph/core/workspace"  # Include SDK source for sdist builds
]
```

**Why include SDK in sdist?**
- Source distributions need the SDK to run `prepare_build.py`
- When users install from sdist, the build hook can copy workspace files
- Wheel distributions already have workspace files baked in

## What Gets Packaged?

### ✅ Included in Wheel
- `glyph_forge/` - Main package
- `glyph_forge/core/client/` - HTTP client
- `glyph_forge/core/workspace/` - Workspace module (copied from SDK)
- Dependencies: `httpx>=0.25.0`

### ❌ NOT Included in Wheel
- `sdk/` - Git submodule (not packaged)
- `scripts/` - Build scripts
- `tests/` - Test suite
- `hatch_build.py` - Build hook

## Verification

### Check wheel contents:
```bash
unzip -l dist/glyph_forge-*.whl
```

### Verify no SDK directory:
```bash
unzip -l dist/glyph_forge-*.whl | grep -i sdk  # Should return nothing
```

### Verify workspace included:
```bash
unzip -l dist/glyph_forge-*.whl | grep workspace  # Should show workspace files
```

## GitHub Actions Workflow

The `.github/workflows/release.yml` handles automated publishing:

### Trigger
- Automatic when `src/glyph_forge/_version.py` changes

### Build Process
```yaml
- name: Build wheel and sdist
  run: |
    python -m pip install --upgrade pip build
    rm -rf dist build *.egg-info
    python -m build  # Runs hatch_build.py hook automatically
    python -m pip install --upgrade twine
    python -m twine check dist/*
```

**Important:**
- `submodules: true` in checkout ensures SDK is available
- Build hook runs automatically via hatchling
- Both wheel and sdist are built

### Publishing
1. **TestPyPI** - Always published when version changes
2. **PyPI** - Only published for non-pre-release versions

## Development Workflow

### Local Development
```bash
# Install in editable mode
pip install -e .

# Run tests
pytest tests/

# Build locally
python -m build
```

### Updating Workspace Code

When SDK workspace code changes:

1. **Update submodule:**
   ```bash
   cd sdk
   git pull origin main
   cd ..
   git add sdk
   git commit -m "Update SDK submodule"
   ```

2. **Test locally:**
   ```bash
   python scripts/prepare_build.py  # Copy workspace files
   pytest tests/                     # Run tests
   ```

3. **Build and verify:**
   ```bash
   python -m build
   unzip -l dist/*.whl  # Verify contents
   ```

## Import Path Strategy

### SDK (submodule):
```python
from glyph.core.workspace import create_workspace
```

### Client Package:
```python
from glyph_forge.core.workspace import create_workspace
# OR
from glyph_forge import create_workspace
```

**Why different paths?**
- Avoids namespace conflicts
- SDK can be developed independently
- Client package has clean public API

## Best Practices

1. **Never manually edit `src/glyph_forge/core/workspace/`**
   - These files are auto-generated from SDK
   - Edit SDK source, then run `prepare_build.py`

2. **Always run `prepare_build.py` after updating SDK**
   ```bash
   python scripts/prepare_build.py
   ```

3. **Test before releasing**
   ```bash
   # Build locally
   python -m build

   # Install from wheel
   pip install dist/glyph_forge-*.whl

   # Test imports
   python -c "from glyph_forge import ForgeClient, create_workspace"
   ```

4. **Version bumping**
   ```bash
   # Edit src/glyph_forge/_version.py
   echo '__version__ = "0.1.0"' > src/glyph_forge/_version.py
   git add src/glyph_forge/_version.py
   git commit -m "Bump version to 0.1.0"
   git push  # Triggers release workflow
   ```

## Troubleshooting

### Issue: Workspace module not in wheel
**Solution:** Check `artifacts` in `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
artifacts = [
  "src/glyph_forge/core/workspace/**/*.py",
]
```

### Issue: SDK code included in wheel
**Solution:** Verify `packages` only includes `src/glyph_forge`:
```toml
packages = ["src/glyph_forge"]
```

### Issue: Import errors after installation
**Solution:** Run `prepare_build.py` to ensure workspace files are copied:
```bash
python scripts/prepare_build.py
```

### Issue: Build hook not running
**Solution:** Check `hatch_build.py` is configured:
```toml
[tool.hatch.build.hooks.custom]
path = "hatch_build.py"
```

## Summary

✅ **Only `src/glyph_forge/` is packaged** (no SDK directory)
✅ **Workspace code is copied during build** (via `prepare_build.py`)
✅ **Artifacts setting ensures workspace files are included** in wheel
✅ **GitHub Actions automates the entire process**
✅ **No redundant code in final package**