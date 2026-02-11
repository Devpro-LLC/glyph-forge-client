"""
Image Document Sample
=====================

Demonstrates the ForgeClient workflow for a DOCX document that contains
embedded images.

Pipeline:
    1. Build schema + markup from a DOCX with images
    2. Inspect extracted image metadata in the schema
    3. Edit markup (images appear as $glyph-image-id-* blocks)
    4. Run the schema to produce a new DOCX with images preserved

Key concepts:
    - Images are extracted during build and tracked in schema["images"]
    - Each image gets an id (e.g. "img_1") and rel_path (e.g. "media/image1.png")
    - Markup emits $glyph-image-id-img_1-image-width-2in-image-height-1in blocks
    - At run time the runner re-extracts images from the embedded source DOCX
      and builds an ImageRegistry so the ImageWriter can resolve them
"""

from __future__ import annotations

import json
from pathlib import Path

from glyph_forge import ForgeClient, create_workspace


# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------

SAMPLE_DOCX = "samples/input/report_with_images.docx"  # DOCX containing images

client = ForgeClient()
ws = create_workspace(use_uuid=True)

print(f"[workspace] run_id = {ws.run_id}")
print(f"[workspace] root   = {ws.root_dir}")


# ------------------------------------------------------------------------------
# 1) Build schema + markup from the DOCX
# ------------------------------------------------------------------------------

result = client.build_glyph_from_docx(
    ws,
    docx_path=SAMPLE_DOCX,
    save_as="report_with_images",
)

schema = result["schema"]
markup = result["markup"]

print(f"\n[build] selectors:  {len(schema.get('selectors', schema.get('pattern_descriptors', [])))}")
print(f"[build] markup:     {len(markup)} chars")


# ------------------------------------------------------------------------------
# 2) Inspect image metadata
# ------------------------------------------------------------------------------

images = schema.get("images", [])
print(f"\n[images] {len(images)} image(s) found in schema:")

for img in images:
    print(f"  - id: {img['id']}")
    print(f"    rel_path:     {img.get('rel_path', 'N/A')}")
    print(f"    dimensions:   {img.get('width_inches', '?')}in x {img.get('height_inches', '?')}in")
    print(f"    alt_text:     {img.get('alt_text', '')[:60] or '(none)'}")


# ------------------------------------------------------------------------------
# 3) Show the image blocks in markup
#
#    Each image appears as a $glyph block with image utilities:
#
#        $glyph-image-id-img_1-image-width-2in-image-height-1in
#        Alt text for the image
#        $glyph
#
#    You can edit these blocks to change dimensions, alignment, etc.
#    Supported image utilities:
#        image-id-{id}           — links to schema images array
#        image-width-{N}in       — width in inches
#        image-height-{N}in      — height in inches
#        image-align-{left|center|right}
#        image-caption-below     — treat block text as caption
#        image-path-{path}       — direct file path (local use only)
# ------------------------------------------------------------------------------

print(f"\n[markup] Image blocks in generated markup:")
for line in markup.splitlines():
    if "$glyph-image-id-" in line:
        print(f"  {line}")


# ------------------------------------------------------------------------------
# 4) (Optional) Edit the markup
#
#    For example, center-align all images and change a width:
# ------------------------------------------------------------------------------

edited_markup = markup.replace(
    "$glyph-image-id-img_1",
    "$glyph-image-id-img_1-image-align-center",
)

print(f"\n[edit] Added center alignment to img_1")


# ------------------------------------------------------------------------------
# 5) Run the schema to produce output DOCX
#
#    The runner:
#    a) Decodes the embedded source DOCX (source_docx_base64 in schema)
#    b) Extracts word/media/* to a temp directory
#    c) Builds an ImageRegistry mapping image IDs -> extracted paths
#    d) Passes the registry to ImageWriter via SchemaRouter
#    e) ImageWriter resolves each IMG descriptor's image_id through the registry
# ------------------------------------------------------------------------------

output_path = client.run_schema(
    ws,
    schema=schema,
    plaintext=edited_markup,
    dest_name="report_with_images_output.docx",
)

print(f"\n[run] Output DOCX saved to: {output_path}")


# ------------------------------------------------------------------------------
# 6) Verify the output contains images
# ------------------------------------------------------------------------------

import zipfile

with zipfile.ZipFile(output_path, "r") as zf:
    media_files = [n for n in zf.namelist() if "media/" in n]

print(f"[verify] Output DOCX contains {len(media_files)} media file(s):")
for f in media_files:
    print(f"  - {f}")

print("\ndone.")
