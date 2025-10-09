#!/usr/bin/env python3
"""
Unit test to validate styling through the complete ForgeClient pipeline.

Tests the complete workflow using ForgeClient:
1. Build workspace
2. Build schema from hello_world.docx (has red/bold text)
3. Verify schema captures red/bold styling
4. Run schema with plaintext
5. Verify output DOCX preserves red/bold styling, correct page size, and margins
"""

import pytest
import zipfile
import tempfile
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

from glyph_forge import ForgeClient, create_workspace


# Paths
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
TEMPLATE_DOCX = EXAMPLES_DIR / "test_data" / "docx" / "hello_world.docx"
INPUT_TEXT_FILE = EXAMPLES_DIR / "test_data" / "plaintext" / "helloworld.txt"
API_KEY = "glyph_sk_live_WPqVQJ9aDJStsbmDaQGAw6YX-1qmFr4l"


# XML namespaces for Word documents
NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
}


def extract_docx_xml(docx_path: Path) -> ET.Element:
    """Extract and parse document.xml from a DOCX file."""
    with zipfile.ZipFile(docx_path, 'r') as zf:
        with zf.open('word/document.xml') as xml_file:
            return ET.parse(xml_file).getroot()


def get_first_run_properties(xml_root: ET.Element) -> dict:
    """
    Extract formatting properties from the first text run in the document.

    Returns dict with keys: bold, color, size, font_name, etc.
    """
    # Find first paragraph with text
    paragraphs = xml_root.findall('.//w:p', NS)

    for para in paragraphs:
        # Find first run with text
        runs = para.findall('.//w:r', NS)
        for run in runs:
            text_elem = run.find('.//w:t', NS)
            if text_elem is not None and text_elem.text:
                # Extract run properties
                rPr = run.find('.//w:rPr', NS)
                if rPr is not None:
                    props = {}

                    # Check for bold
                    bold = rPr.find('.//w:b', NS)
                    props['bold'] = bold is not None

                    # Check for italic
                    italic = rPr.find('.//w:i', NS)
                    props['italic'] = italic is not None

                    # Check for color
                    color = rPr.find('.//w:color', NS)
                    if color is not None:
                        props['color'] = color.get('{%s}val' % NS['w'])

                    # Check for size
                    size = rPr.find('.//w:sz', NS)
                    if size is not None:
                        props['size'] = int(size.get('{%s}val' % NS['w']))

                    # Check for font name
                    font = rPr.find('.//w:rFonts', NS)
                    if font is not None:
                        props['font_name'] = font.get('{%s}ascii' % NS['w'])

                    return props

    return {}


def get_page_properties(xml_root: ET.Element) -> dict:
    """
    Extract page size and margins from document.xml.

    Returns dict with keys: width, height, margin_top, margin_left, etc.
    """
    # Find sectPr (section properties)
    sectPr = xml_root.find('.//w:sectPr', NS)
    if sectPr is None:
        return {}

    props = {}

    # Page size
    pgSz = sectPr.find('.//w:pgSz', NS)
    if pgSz is not None:
        props['width'] = int(pgSz.get('{%s}w' % NS['w']))
        props['height'] = int(pgSz.get('{%s}h' % NS['w']))

    # Margins
    pgMar = sectPr.find('.//w:pgMar', NS)
    if pgMar is not None:
        props['margin_top'] = int(pgMar.get('{%s}top' % NS['w']))
        props['margin_right'] = int(pgMar.get('{%s}right' % NS['w']))
        props['margin_bottom'] = int(pgMar.get('{%s}bottom' % NS['w']))
        props['margin_left'] = int(pgMar.get('{%s}left' % NS['w']))

    return props


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="test_hello_world_")
    ws = create_workspace(root_dir=temp_dir, use_uuid=False)
    yield ws
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def forge_client():
    """Create a ForgeClient instance."""
    client = ForgeClient(api_key=API_KEY)
    yield client
    client.close()


class TestHelloWorldStylePipeline:
    """Test styling preservation through build_schema -> run_schema pipeline using ForgeClient."""

    def test_complete_pipeline_preserves_styling(self, temp_workspace, forge_client):
        """
        Complete end-to-end test:
        1. Build schema from hello_world.docx (has red/bold text)
        2. Verify schema captures styling
        3. Run schema with plaintext
        4. Verify output preserves styling, page size, and margins
        """
        ws = temp_workspace
        client = forge_client

        # Verify input files exist
        assert TEMPLATE_DOCX.exists(), f"Template DOCX not found: {TEMPLATE_DOCX}"
        assert INPUT_TEXT_FILE.exists(), f"Input text file not found: {INPUT_TEXT_FILE}"

        # Read input text
        with open(INPUT_TEXT_FILE, 'r') as f:
            plaintext = f.read()

        # Step 1: Extract original DOCX properties for comparison
        print("\n[1] Extracting original DOCX properties...")
        original_xml = extract_docx_xml(TEMPLATE_DOCX)
        original_style = get_first_run_properties(original_xml)
        original_page = get_page_properties(original_xml)

        print(f"  Original style: {original_style}")
        print(f"  Original page: {original_page}")

        assert original_style.get('bold') == True, "Original DOCX should have bold text"
        assert original_style.get('color') is not None, "Original DOCX should have color"
        assert original_page.get('width') == 12240, "Original DOCX should have 8.5\" width (12240 twips)"
        assert original_page.get('height') == 15840, "Original DOCX should have 11\" height (15840 twips)"

        # Step 2: Build schema using ForgeClient
        print("\n[2] Building schema using ForgeClient...")
        schema = client.build_schema_from_docx(
            ws,
            docx_path=str(TEMPLATE_DOCX),
            save_as="test_hello_world_schema",
            include_artifacts=True
        )

        # Step 3: Verify schema captured styling
        print("\n[3] Verifying schema captured styling...")
        pattern_descriptors = schema.get('pattern_descriptors', [])
        assert len(pattern_descriptors) > 0, "Schema should have pattern descriptors"

        first_desc = pattern_descriptors[0]
        schema_style = first_desc.get('style', {})
        schema_font = schema_style.get('font', {})

        print(f"  Schema style: {schema_style}")
        print(f"  Schema font: {schema_font}")

        assert schema_font.get('bold') == True, f"Schema should capture bold=True, got: {schema_font}"
        assert schema_font.get('color') is not None, f"Schema should capture color, got: {schema_font}"

        # Verify schema captured page size
        global_defaults = schema.get('global_defaults', {})
        page_size = global_defaults.get('page_size', {})
        margins = global_defaults.get('margins', {})

        print(f"  Schema page_size: {page_size}")
        print(f"  Schema margins: {margins}")

        assert page_size.get('width') == 12240, f"Schema should capture width=12240, got: {page_size}"
        assert page_size.get('height') == 15840, f"Schema should capture height=15840, got: {page_size}"
        assert margins.get('left') == 1440, f"Schema should capture margins, got: {margins}"

        # Step 4: Run schema using ForgeClient
        print("\n[4] Running schema with plaintext using ForgeClient...")
        output_docx_path = client.run_schema(
            ws,
            schema=schema,
            plaintext=plaintext,
            dest_name="test_hello_world_output.docx"
        )

        assert Path(output_docx_path).exists(), f"Output DOCX should exist at: {output_docx_path}"

        # Step 5: Verify output DOCX preserves styling and page properties
        print("\n[5] Verifying output DOCX preserves styling and page properties...")
        output_xml = extract_docx_xml(Path(output_docx_path))
        output_style = get_first_run_properties(output_xml)
        output_page = get_page_properties(output_xml)

        print(f"  Output style: {output_style}")
        print(f"  Output page: {output_page}")

        # Assertions for styling
        assert output_style.get('bold') == True, \
            f"Output DOCX should preserve bold. Original: {original_style.get('bold')}, Output: {output_style.get('bold')}"

        assert output_style.get('color') is not None, \
            f"Output DOCX should preserve color. Original: {original_style.get('color')}, Output: {output_style.get('color')}"

        # Color should match (allowing for case differences)
        original_color = original_style.get('color', '').upper()
        output_color = output_style.get('color', '').upper()
        assert original_color == output_color, \
            f"Color mismatch. Original: {original_color}, Output: {output_color}"

        # Assertions for page properties
        assert output_page.get('width') == 12240, \
            f"Output DOCX should preserve page width. Expected: 12240, Got: {output_page.get('width')}"

        assert output_page.get('height') == 15840, \
            f"Output DOCX should preserve page height. Expected: 15840, Got: {output_page.get('height')}"

        assert output_page.get('margin_left') == 1440, \
            f"Output DOCX should preserve margins. Expected: 1440, Got: {output_page.get('margin_left')}"

        # Final comparison
        print("\n[✓] All assertions passed!")
        print(f"  Original → Output style match: {original_style} → {output_style}")
        print(f"  Original → Output page match: {original_page} → {output_page}")


if __name__ == "__main__":
    # Run with: pytest tests/client/test_hello_world_styling.py -v -s
    pytest.main([__file__, "-v", "-s"])
