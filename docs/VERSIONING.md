# Versioning Strategy for glyph-forge-client

## Overview

This project uses **automated version-based releases** following Python packaging best practices. Any change to `src/glyph_forge/_version.py` triggers the build and publishing workflow.

## Version Format

We follow [Semantic Versioning](https://semver.org/) with [PEP 440](https://peps.python.org/pep-0440/) for pre-releases:

```
MAJOR.MINOR.PATCH[pre-release][dev]
```

### Examples

**Stable Releases** (→ TestPyPI + PyPI):
- `0.1.0` - First minor release
- `1.0.0` - First major release
- `1.2.3` - Patch release

**Pre-releases** (→ TestPyPI only):
- `0.1.0a1` - Alpha 1
- `0.1.0b1` - Beta 1
- `0.1.0rc1` - Release candidate 1
- `0.1.0.dev1` - Development build

## Single Source of Truth

**File:** `src/glyph_forge/_version.py`

```python
__version__ = "0.1.0"
```

**Why this file?**
- Industry standard for Python packages
- Read by `hatchling` via `pyproject.toml`:
  ```toml
  [project]
  dynamic = ["version"]

  [tool.hatch.version]
  path = "src/glyph_forge/_version.py"
  ```
- Simple: one file, one line
- No external tools required

## Release Workflow

### 1. Development → Pre-release

```bash
# Make changes...
git add .
git commit -m "Add new feature"

# Bump to pre-release version
echo '__version__ = "0.2.0a1"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Bump version to 0.2.0a1"
git push origin main
```

**What happens:**
1. ✅ GitHub Actions detects `_version.py` changed
2. ✅ Builds wheel + sdist
3. ✅ Publishes to **TestPyPI only** (pre-release detected)
4. ❌ Skips PyPI (pre-release)

**Install test version:**
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ glyph-forge==0.2.0a1
```

### 2. Testing → Release Candidate

```bash
# After testing, bump to RC
echo '__version__ = "0.2.0rc1"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Bump version to 0.2.0rc1"
git push origin main
```

**What happens:**
- Same as pre-release: TestPyPI only

### 3. Production → Stable Release

```bash
# Ready for production
echo '__version__ = "0.2.0"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Release v0.2.0"
git push origin main
```

**What happens:**
1. ✅ GitHub Actions detects `_version.py` changed
2. ✅ Builds wheel + sdist
3. ✅ Publishes to **TestPyPI** (all versions go here)
4. ✅ Publishes to **PyPI** (stable release detected)

**Users can now install:**
```bash
pip install glyph-forge==0.2.0
# or
pip install glyph-forge  # gets latest stable
```

## Version Detection Logic

From `.github/workflows/release.yml`:

```yaml
# Detects pre-release by checking for these markers:
if echo "$VER" | grep -Eq '(a|b|rc|dev)'; then
  is_prerelease=true  # → TestPyPI only
else
  is_prerelease=false  # → TestPyPI + PyPI
fi
```

**Patterns recognized as pre-release:**
- `a`, `alpha` - Alpha releases
- `b`, `beta` - Beta releases
- `rc` - Release candidates
- `dev` - Development builds

## Automation Details

### Workflow Triggers

1. **Automatic** - Push to `main` branch
   - Only runs if `_version.py` changed
   - Supports both direct commits and merge commits

2. **Manual** - Via GitHub UI
   - Go to Actions → Release workflow → "Run workflow"
   - Useful for re-running failed builds

### Publishing Targets

**TestPyPI** (test.pypi.org):
- All versions (stable + pre-release)
- Requires `TEST_PYPI_API_TOKEN` secret
- Use for testing before production

**PyPI** (pypi.org):
- Stable versions only
- Uses Trusted Publishing (OIDC) - no API key needed
- Production repository

### GitHub Secrets Required

| Secret | Purpose | How to get |
|--------|---------|------------|
| `TEST_PYPI_API_TOKEN` | Publish to TestPyPI | https://test.pypi.org/manage/account/token/ |

**Note:** PyPI uses Trusted Publishing, so no secret needed!

## Semantic Versioning Rules

### When to bump MAJOR (X.0.0)
- Breaking API changes
- Removed features
- Major architecture changes

Example:
```python
# Before (v1.0.0)
client = ForgeClient(api_key="...")

# After (v2.0.0) - BREAKING
client = ForgeClient()  # No api_key parameter
```

### When to bump MINOR (0.X.0)
- New features (backwards-compatible)
- New API methods
- Significant enhancements

Example:
```python
# v0.1.0 has: build_schema_from_docx()
# v0.2.0 adds: build_schema_from_template() ← NEW
```

### When to bump PATCH (0.0.X)
- Bug fixes
- Documentation updates
- Internal refactoring (no API changes)

Example:
```python
# v0.1.0 - Bug: timeout not working
# v0.1.1 - Fixed: timeout now properly applied
```

## Best Practices

### ✅ DO

1. **Always use pre-releases for testing**
   ```bash
   0.2.0a1 → 0.2.0rc1 → 0.2.0
   ```

2. **Commit version changes separately**
   ```bash
   git commit -m "Bump version to 0.2.0"
   ```

3. **Tag stable releases** (optional but recommended)
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

4. **Test from TestPyPI before stable release**
   ```bash
   pip install --index-url https://test.pypi.org/simple/ \
               --extra-index-url https://pypi.org/simple/ \
               glyph-forge==0.2.0rc1
   ```

### ❌ DON'T

1. **Don't skip pre-releases for major changes**
   ```bash
   # Bad: 0.1.0 → 0.2.0 (big new feature, no testing)
   # Good: 0.1.0 → 0.2.0a1 → 0.2.0rc1 → 0.2.0
   ```

2. **Don't manually edit `pyproject.toml` version**
   ```toml
   # This is managed by hatchling automatically
   [project]
   dynamic = ["version"]  # ← Don't remove this
   ```

3. **Don't reuse version numbers**
   ```bash
   # If 0.2.0 is already on PyPI, you CANNOT republish it
   # Must use 0.2.1 or 0.3.0
   ```

4. **Don't commit version changes with code changes**
   ```bash
   # Bad:
   git commit -m "Add feature X and bump to 0.2.0"

   # Good:
   git commit -m "Add feature X"
   git commit -m "Bump version to 0.2.0"
   ```

## Quick Reference

### Development Workflow

```bash
# 1. Make changes
git checkout -b feature/new-thing
# ... code changes ...
git commit -m "Add new feature"
git push origin feature/new-thing

# 2. Create PR, review, merge to main

# 3. Release alpha for testing
echo '__version__ = "0.2.0a1"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Bump version to 0.2.0a1"
git push origin main
# → Publishes to TestPyPI only

# 4. Test installation
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            glyph-forge==0.2.0a1

# 5. If tests pass, release stable
echo '__version__ = "0.2.0"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Release v0.2.0"
git push origin main
# → Publishes to TestPyPI + PyPI
```

### Hotfix Workflow

```bash
# For urgent bugfix on production version
git checkout -b hotfix/critical-bug main

# Fix the bug...
git commit -m "Fix critical bug"

# Bump patch version
echo '__version__ = "0.1.1"' > src/glyph_forge/_version.py
git add src/glyph_forge/_version.py
git commit -m "Bump version to 0.1.1"

# Merge and push
git checkout main
git merge hotfix/critical-bug
git push origin main
# → Publishes to TestPyPI + PyPI immediately
```

## Troubleshooting

### Problem: Workflow didn't run

**Check:**
1. Was `_version.py` actually changed?
   ```bash
   git show HEAD --name-only | grep _version
   ```

2. Are you on the `main` branch?
   ```bash
   git branch --show-current
   ```

### Problem: TestPyPI publish failed

**Common causes:**
- Version already exists on TestPyPI
- Missing `TEST_PYPI_API_TOKEN` secret
- Token expired or revoked

**Solution:**
- Use a new version number
- Regenerate token at https://test.pypi.org/manage/account/token/

### Problem: PyPI publish failed

**Common causes:**
- Version already exists on PyPI (versions are permanent!)
- Trusted Publishing not configured
- Pre-release leaked to PyPI (should only go to TestPyPI)

**Solution:**
- Use a new version number
- Configure Trusted Publishing at https://pypi.org/manage/project/glyph-forge/settings/publishing/

### Problem: Build failed

**Common causes:**
- Syntax error in `_version.py`
- SDK submodule not initialized
- Dependencies missing

**Check workflow logs:**
1. Go to Actions tab in GitHub
2. Click on failed workflow run
3. Check build logs

## Alternative Approaches (Not Currently Used)

### Automated Version Bumping

Some projects use tools like:
- **bump2version** / **bumpversion**
- **semantic-release**
- **setuptools-scm** (version from git tags)

**Why we don't use them:**
- Manual control = explicit intent
- Simple = fewer dependencies
- Clear = easy to understand and audit

### Git Tag-based Versioning

```bash
git tag v0.2.0
git push --tags
```

**Why we don't use it:**
- Requires tag push (extra step)
- Can't do pre-releases easily
- `_version.py` is simpler and more explicit

## Future Enhancements

### Option 1: Add Changelog Generation

```yaml
- name: Generate Changelog
  uses: release-drafter/release-drafter@v5
  with:
    config-name: release-drafter.yml
```

### Option 2: Add Git Tags on Release

```yaml
- name: Create Git Tag
  if: needs.detect-version-change.outputs.is_prerelease == 'false'
  run: |
    git tag -a "v${{ needs.detect-version-change.outputs.version }}" \
            -m "Release v${{ needs.detect-version-change.outputs.version }}"
    git push origin "v${{ needs.detect-version-change.outputs.version }}"
```

### Option 3: Add GitHub Release

```yaml
- name: Create GitHub Release
  uses: softprops/action-gh-release@v1
  if: needs.detect-version-change.outputs.is_prerelease == 'false'
  with:
    tag_name: v${{ needs.detect-version-change.outputs.version }}
    name: Release v${{ needs.detect-version-change.outputs.version }}
    files: dist/*
```

## Summary

✅ **Current strategy is solid and follows industry best practices**
✅ **Single source of truth** (`_version.py`)
✅ **Automated publishing** (TestPyPI + PyPI)
✅ **Pre-release support** (test before production)
✅ **Secure** (Trusted Publishing for PyPI)
✅ **Scalable** (works for teams and solo devs)

**No major changes needed** - your current approach is production-ready!