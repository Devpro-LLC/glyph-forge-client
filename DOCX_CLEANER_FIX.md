# CRITICAL FIX: docx_cleaner.py Page Size & Style Preservation

## Problem Statement

When generating DOCX output from schema, two critical issues occur:

1. **Page size minimized to ~1" x 1"** - Output document has tiny page dimensions
2. **All styles default to "Normal"** - Heading1, List Paragraph, etc. are not applied

## Root Cause

**File:** `sdk/src/glyph/core/schema_runner/utils/docx_cleaner.py`

**Current broken logic (lines 11-14):**

```python
# start from a default sectPr
default_doc = Document()  # ← Creates NEW blank document with 1"x1" page
sectPr = default_doc.element.body.sectPr  # ← Gets WRONG sectPr from blank doc
```

**What's happening:**

1. Line 5: `doc = Document(path)` - Loads the tagged input DOCX correctly (has proper page size, styles)
2. Line 9-10: Removes ALL body content **including the original sectPr** (section properties)
3. **Line 13-14: MISTAKE** - Creates a brand NEW blank document and takes its sectPr
4. Line 57: Appends this broken sectPr to the stripped body
5. Result: Output has blank document's settings (tiny page, no custom styles)

**The fundamental issue:** We're throwing away the original document's sectPr and replacing it with a blank one.

---

## Solution: Preserve Original sectPr

The original tagged input DOCX (`examples/outputs/default/input/docx/resume_<tag>.docx`) already has:

- ✅ Correct page size (8.5" × 11")
- ✅ Proper margins (1" all sides)
- ✅ All style definitions (Heading1, List Paragraph, etc. in styles.xml)
- ✅ Theme colors and fonts

**We should PRESERVE these and only MODIFY them with global_defaults, not replace them.**

---

## Implementation Instructions

### Step 1: Update `strip_body_content()` Function

**File:** `sdk/src/glyph/core/schema_runner/utils/docx_cleaner.py`

**Replace the entire function (lines 4-39) with:**

```python
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def strip_body_content(path: str, global_default: dict | None = None) -> Document:
    """
    Strip body content from source DOCX while preserving section properties and styles.

    CRITICAL: The source DOCX (tagged input) contains:
    - Page size/margins in sectPr
    - Style definitions in styles.xml
    - Theme colors/fonts

    This function PRESERVES these properties and optionally MODIFIES them with global_defaults.

    Args:
        path: Path to source DOCX (e.g., examples/outputs/default/input/docx/resume_<tag>.docx)
        global_default: Optional dict with global_defaults to override section properties

    Returns:
        Document with body content removed but styles/section properties preserved
    """
    # Load the original tagged input DOCX
    doc = Document(path)
    body = doc.element.body

    # CRITICAL: Preserve original sectPr BEFORE removing children
    original_sectPr = body.sectPr

    if original_sectPr is None:
        # Fallback: create minimal sectPr if source doesn't have one
        # (This should rarely happen with real DOCX files)
        original_sectPr = OxmlElement('w:sectPr')

    # Remove all children (paragraphs, tables) but keep sectPr
    for child in list(body):
        # Don't remove sectPr - we need to preserve it!
        if child.tag != qn('w:sectPr'):
            body.remove(child)

    # Now modify the ORIGINAL sectPr with global_defaults (if provided)
    if global_default:
        gd = global_default.get("global_defaults", global_default)
        sectPr = original_sectPr

        # Page size - handle both nested and flat structure
        page_size = gd.get("page_size", {})
        if "width" in page_size:
            sectPr.pgSz.w = page_size["width"]
        elif "page_width" in gd:
            sectPr.pgSz.w = gd["page_width"]

        if "height" in page_size:
            sectPr.pgSz.h = page_size["height"]
        elif "page_height" in gd:
            sectPr.pgSz.h = gd["page_height"]

        if "orientation" in gd:
            sectPr.pgSz.orient = gd["orientation"]

        # Margins - handle both nested and flat structure
        margins = gd.get("margins", {})
        if "left" in margins:
            sectPr.pgMar.left = margins["left"]
        elif "left_margin" in gd:
            sectPr.pgMar.left = gd["left_margin"]

        if "right" in margins:
            sectPr.pgMar.right = margins["right"]
        elif "right_margin" in gd:
            sectPr.pgMar.right = gd["right_margin"]

        if "top" in margins:
            sectPr.pgMar.top = margins["top"]
        elif "top_margin" in gd:
            sectPr.pgMar.top = gd["top_margin"]

        if "bottom" in margins:
            sectPr.pgMar.bottom = margins["bottom"]
        elif "bottom_margin" in gd:
            sectPr.pgMar.bottom = gd["bottom_margin"]

    # NOTE: sectPr is already in body, don't re-append!
    # The old code was appending a new sectPr, which was wrong.

    return doc
```

---

### Step 2: Add Import for `qn` (if not already present)

**At the top of `docx_cleaner.py`:**

```python
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn  # ← Add this import
```

---

### Step 3: Update Tests (if needed)

**File:** `sdk/tests/schema_runner/test_docx_cleaner.py`

Add a test to verify sectPr is preserved:

```python
def test_strip_body_preserves_section_properties(tmp_path):
    """Verify that stripping body preserves original sectPr."""
    from docx import Document
    from glyph.core.schema_runner.utils.docx_cleaner import strip_body_content

    # Create a test DOCX with known page size
    test_docx = tmp_path / "test.docx"
    doc = Document()
    doc.sections[0].page_width = 12240  # 8.5 inches
    doc.sections[0].page_height = 15840  # 11 inches
    doc.add_paragraph("Test content")
    doc.save(str(test_docx))

    # Strip body content
    stripped = strip_body_content(str(test_docx))

    # Verify page size is preserved
    assert stripped.sections[0].page_width == 12240
    assert stripped.sections[0].page_height == 15840

    # Verify content is removed
    assert len(stripped.paragraphs) == 0

def test_strip_body_applies_global_defaults(tmp_path):
    """Verify global_defaults override original sectPr."""
    from docx import Document
    from glyph.core.schema_runner.utils.docx_cleaner import strip_body_content

    # Create test DOCX
    test_docx = tmp_path / "test.docx"
    doc = Document()
    doc.sections[0].page_width = 10000  # Different size
    doc.save(str(test_docx))

    # Apply global_defaults
    global_defaults = {
        "page_size": {"width": 12240, "height": 15840},
        "margins": {"left": 1440, "right": 1440, "top": 1440, "bottom": 1440}
    }

    stripped = strip_body_content(str(test_docx), global_defaults)

    # Verify global_defaults were applied
    assert stripped.sections[0].page_width == 12240
    assert stripped.sections[0].page_height == 15840
    assert stripped.sections[0].left_margin == 1440
```

---

### Step 4: Handle source_docx_base64 in run_schema.py ⭐ CRITICAL

**File:** `sdk/src/glyph/core/schema_runner/run_schema.py`

**Problem:** The schema contains the tagged DOCX as **base64-encoded data** in `schema["source_docx_base64"]`, but the current code only looks for `schema["source_docx"]` (a file path).

**Current broken code (lines 37-41):**

```python
docx_path = source_docx or schema.get("source_docx")  # ← Misses source_docx_base64!
if not docx_path:
    raise ValueError("No source_docx provided (param or schema).")

self.document: Document = strip_body_content(str(docx_path), self.global_defaults)
```

**The Fix - Replace with:**

```python
# Handle source DOCX from multiple sources
if source_docx:
    # Explicit parameter takes priority
    docx_path = source_docx
elif "source_docx" in schema:
    # File path in schema
    docx_path = schema["source_docx"]
elif "source_docx_base64" in schema:
    # CRITICAL: Decode base64 embedded DOCX and save to workspace
    import base64
    import tempfile
    from pathlib import Path

    # Decode base64 data
    docx_data = base64.b64decode(schema["source_docx_base64"])

    # Determine save location
    tag = schema.get("tag", "temp")

    # Try to save in workspace input directory if available
    if hasattr(self, 'settings') and hasattr(self.settings, 'workspace'):
        workspace = self.settings.workspace
        if hasattr(workspace, 'paths') and "input_docx" in workspace.paths:
            input_docx_dir = Path(workspace.paths["input_docx"])
            input_docx_dir.mkdir(parents=True, exist_ok=True)
            docx_path = input_docx_dir / f"source_{tag}.docx"
        else:
            # Fallback to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
            docx_path = Path(temp_file.name)
            temp_file.close()
    else:
        # Fallback to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        docx_path = Path(temp_file.name)
        temp_file.close()

    # Write decoded DOCX data to file
    docx_path.write_bytes(docx_data)
    docx_path = str(docx_path)
else:
    raise ValueError(
        "No source_docx provided. Expected one of:\n"
        "  - source_docx parameter\n"
        "  - schema['source_docx'] (file path)\n"
        "  - schema['source_docx_base64'] (embedded DOCX)"
    )

# Now strip body content from the tagged DOCX
self.document: Document = strip_body_content(str(docx_path), self.global_defaults)
```

**Why This is Critical:**

The schema returned by `ForgeClient.build_schema_from_docx()` contains:

```json
{
  "source_docx_base64": "UEsDBBQABgAIAAAAIQAJaicN...",  // ← Tagged DOCX with styles.xml
  "pattern_descriptors": [...],
  "global_defaults": {...}
}
```

Without decoding and using this tagged DOCX:
- ❌ No file path exists
- ❌ Can't load the document
- ❌ Error: "No source_docx provided"

**With the fix:**
- ✅ Decodes base64 → binary DOCX
- ✅ Saves to workspace: `{workspace}/input/docx/source_{tag}.docx`
- ✅ Passes correct path to `strip_body_content()`
- ✅ Tagged DOCX with proper styles.xml is used as template

---

### Step 5: Verify Source DOCX Path (Updated)

**File:** `sdk/src/glyph/core/schema_runner/run_schema.py`

After implementing Step 4, add debug logging to verify the correct DOCX is loaded:

**After the docx_path resolution (new code above):**

```python
# Debug: Verify we're using the correct source DOCX
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Loading source DOCX: {docx_path}")

# Verify it exists
if not Path(docx_path).exists():
    raise FileNotFoundError(f"Source DOCX not found: {docx_path}")

self.document: Document = strip_body_content(str(docx_path), self.global_defaults)
```

---

## Testing & Validation

### Manual Testing

1. **Rebuild the output:**

```bash
cd /path/to/glyph-forge-client
python examples/scripts/build_and_run_resume1.py
```

2. **Verify the output DOCX:**

Open `examples/outputs/default/output/docx/resume_output.docx` and check:

- ✅ **Page size:** Should be 8.5" × 11" (not tiny!)
- ✅ **Margins:** Should be 1" on all sides
- ✅ **Styles applied:** Headings should use "Heading1" style (visible in Word's style panel)
- ✅ **Fonts correct:** Text should be Arial (from global_defaults), not Calibri

### Automated Testing

Run the schema_runner tests:

```bash
cd sdk
pytest tests/schema_runner/test_docx_cleaner.py -v
```

**Expected:** All tests pass, especially the new preservation tests.

---

## Expected Behavior After Fix

### Before (Broken):

```
Output DOCX:
- Page size: ~1" × 1" (minimized)
- Margins: Undefined or default
- Styles: All "Normal" (no Heading1, List Paragraph)
- Fonts: Default Calibri
```

### After (Fixed):

```
Output DOCX:
- Page size: 8.5" × 11" (from original or global_defaults)
- Margins: 1" all sides (from global_defaults)
- Styles: Heading1, List Paragraph, etc. (from original styles.xml)
- Fonts: Arial (from global_defaults font overrides)
```

---

## Why This Works

1. **Original sectPr preserved:** Page size, margins from tagged input DOCX
2. **Original styles.xml preserved:** Heading1, List Paragraph styles still available
3. **Global defaults applied:** Schema's page_size/margins/fonts override when specified
4. **Style_id + font overrides work:** Writers can apply Heading1 style THEN override font to Arial

---

## Key Differences from Old Code

| Aspect | Old (Broken) | New (Fixed) |
|--------|-------------|-------------|
| **sectPr source** | New blank Document() | Original tagged input DOCX |
| **Page size** | ~1"×1" (blank doc default) | 8.5"×11" (original or global_defaults) |
| **Styles available** | Only "Normal" | All original styles (Heading1, etc.) |
| **Body removal** | Removes sectPr too | Preserves sectPr |
| **sectPr append** | Appends wrong sectPr | Modifies original in-place |

---

## Potential Edge Cases

### Edge Case 1: Source DOCX has no sectPr

**Solution:** Fallback creates minimal sectPr (already handled in code above)

```python
if original_sectPr is None:
    original_sectPr = OxmlElement('w:sectPr')
```

### Edge Case 2: Multiple sections in source DOCX

**Current behavior:** Only preserves first section's sectPr

**Future enhancement:** Preserve all sections, or allow global_defaults to specify which section

### Edge Case 3: Global defaults not provided

**Solution:** Original sectPr is preserved unchanged (correct behavior)

---

## Summary

**Change required:**
1. Preserve original `sectPr` instead of creating new blank one
2. Remove children EXCEPT sectPr
3. Modify original sectPr with global_defaults in-place
4. Don't re-append sectPr (it's already in body)

**Files to modify:**
- `sdk/src/glyph/core/schema_runner/utils/docx_cleaner.py` (main fix)
- `sdk/tests/schema_runner/test_docx_cleaner.py` (add tests)

**Impact:**
- ✅ Page size correct
- ✅ Styles preserved and applied
- ✅ Fonts override correctly
- ✅ Margins applied from global_defaults

**Estimated time:** 15-20 minutes to implement + 10 minutes to test = **~30 minutes total**
