Working with Images
===================

The Glyph SDK provides comprehensive support for working with images in documents, including extraction from DOCX files, inline image rendering in markup, and round-trip workflows.

Overview
--------

The image support feature enables:

* **Image extraction**: Extract images from DOCX with full metadata (dimensions, position, alt text)
* **Inline rendering**: Insert images in Glyph markup with precise control over size and alignment
* **Round-trip workflows**: DOCX → Schema → Plaintext → DOCX with images preserved
* **Workspace management**: Automatic image organization and path tracking

Quick Start
-----------

Rendering Images in Markup
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Create image registry
   registry = ImageRegistry()
   registry.register("logo", "/path/to/logo.png")
   registry.register("chart", "/path/to/chart.jpg")

   # Create markup with images
   markup = """
   $glyph-bold-font-size-18-align-center
   Annual Report
   $glyph

   $glyph-image-id-logo-image-width-2in-image-align-center
   $glyph

   $glyph-image-id-chart-image-width-5in-image-height-3in
   Figure 1: Revenue Growth
   $glyph
   """

   # Render to DOCX
   render_markup_to_docx(markup, output_path="report.docx", image_registry=registry)

Extracting Images from DOCX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder
   from glyph.core.workspace.storage.fs import FilesystemWorkspace

   # Create workspace
   workspace = FilesystemWorkspace(use_uuid=True)

   # Build schema with image extraction
   builder = GlyphSchemaBuilder(
       document_xml_path="extracted/word/document.xml",
       docx_extract_dir="extracted",
       tag="my_project"
   )

   schema = builder.run(workspace=workspace, copy_images=True)

   # Access extracted images
   for img in schema["images"]:
       print(f"Image: {img['id']}")
       print(f"  Size: {img['width_inches']} x {img['height_inches']} inches")
       print(f"  Path: {img['workspace_path']}")

Image Registry
--------------

The ImageRegistry class maps image IDs to file paths for rendering.

Creating a Registry
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.markup.engine.integration import ImageRegistry

   # Create empty registry
   registry = ImageRegistry()

   # Create with pre-populated images
   registry = ImageRegistry(images={
       "logo": "/path/to/logo.png",
       "banner": "/path/to/banner.jpg",
   })

Registering Images
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Register individual images
   registry.register("profile", "/path/to/profile.png")
   registry.register("signature", "/path/to/signature.jpg")

   # Get image path
   path = registry.get_path("profile")  # Returns "/path/to/profile.png"

   # Check if image exists
   if "logo" in registry.images:
       print("Logo is registered")

   # Access via dict-like interface
   path = registry["profile"]  # Same as get_path()

Bulk Registration
~~~~~~~~~~~~~~~~~

Register multiple images from a directory:

.. code-block:: python

   from pathlib import Path

   registry = ImageRegistry()
   image_dir = Path("images/")

   for img_file in image_dir.glob("*.png"):
       # Use filename (without extension) as ID
       img_id = img_file.stem
       registry.register(img_id, str(img_file))

From Schema Images
~~~~~~~~~~~~~~~~~~

When extracting images from a schema:

.. code-block:: python

   from glyph.runner import schema_to_plaintext

   # Build schema (images extracted automatically)
   schema = builder.run(workspace=workspace, copy_images=True)

   # Create registry from schema images
   registry = ImageRegistry()
   for img in schema["images"]:
       registry.register(img["id"], img["workspace_path"])

   # Generate plaintext
   plaintext = schema_to_plaintext(schema)

   # Render with images
   render_markup_to_docx(plaintext, output_path="output.docx", image_registry=registry)

Image Markup Syntax
-------------------

Basic Image Block
~~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-image-id-{key}
   $glyph

**Example:**

.. code-block:: text

   $glyph-image-id-logo
   $glyph

With Dimensions
~~~~~~~~~~~~~~~

Specify width and/or height in inches:

.. code-block:: text

   $glyph-image-id-{key}-image-width-{N}in-image-height-{N}in
   $glyph

**Example:**

.. code-block:: text

   $glyph-image-id-chart-image-width-5in-image-height-3in
   $glyph

   $glyph-image-id-banner-image-width-6in
   $glyph

**Note:** If only width or height is specified, the aspect ratio is preserved.

With Alignment
~~~~~~~~~~~~~~

Control image alignment:

.. code-block:: text

   $glyph-image-id-{key}-image-align-{position}
   $glyph

**Positions:**

* ``left`` - Left-aligned (default)
* ``center`` - Center-aligned
* ``right`` - Right-aligned

**Example:**

.. code-block:: text

   $glyph-image-id-logo-image-width-2in-image-align-center
   $glyph

With Caption
~~~~~~~~~~~~

Add a caption below the image:

.. code-block:: text

   $glyph-image-id-{key}-image-width-{N}in-image-caption-below
   Caption text here
   $glyph

**Example:**

.. code-block:: text

   $glyph-image-id-chart-image-width-5in-image-caption-below
   Figure 1: Quarterly Revenue Growth
   $glyph

With Alt Text
~~~~~~~~~~~~~

Provide alternative text for accessibility:

.. code-block:: text

   $glyph-image-id-{key}-image-alt-{text}
   $glyph

**Example:**

.. code-block:: text

   $glyph-image-id-logo-image-alt-Company Logo
   $glyph

Direct Path
~~~~~~~~~~~

Reference an image by direct file path (instead of using registry):

.. code-block:: text

   $glyph-image-path-{filepath}-image-width-2in
   $glyph

**Example:**

.. code-block:: text

   $glyph-image-path-/tmp/generated_chart.png-image-width-4in
   $glyph

**Note:** This requires the file to exist at render time.

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-image-id-sales_chart-image-width-5in-image-height-3.5in-image-align-center-image-caption-below
   Figure 1: Q4 Sales Performance by Region
   $glyph

Image Extraction
----------------

The schema builder extracts images from DOCX with comprehensive metadata.

Extraction Process
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder

   builder = GlyphSchemaBuilder(
       document_xml_path="extracted/word/document.xml",
       docx_extract_dir="extracted",  # Required for image extraction
   )

   schema = builder.run()

   # Access extracted images
   images = schema["images"]

Image Metadata
~~~~~~~~~~~~~~

Each extracted image includes:

* ``id``: Unique identifier (e.g., "img_1", "img_2")
* ``name``: Image name from DOCX
* ``path``: Full path to extracted image file
* ``rel_path``: Relative path within DOCX (e.g., "media/image1.png")
* ``rId``: Relationship ID from document.xml.rels
* ``width_inches``: Width in inches (converted from EMUs)
* ``height_inches``: Height in inches (converted from EMUs)
* ``width_emu``: Width in EMUs (English Metric Units)
* ``height_emu``: Height in EMUs
* ``paragraph_index``: Position in document (which paragraph the image appears in)
* ``alt_text``: Alternative text (if specified in DOCX)

**Example:**

.. code-block:: python

   {
       "id": "img_1",
       "name": "Chart",
       "path": "/path/to/extracted/word/media/image1.png",
       "rel_path": "media/image1.png",
       "rId": "rId5",
       "width_inches": 5.0,
       "height_inches": 3.5,
       "width_emu": 4572000,
       "height_emu": 3200400,
       "paragraph_index": 3,
       "alt_text": "Quarterly sales chart"
   }

Copying to Workspace
~~~~~~~~~~~~~~~~~~~~

Automatically copy extracted images to workspace:

.. code-block:: python

   from glyph.core.workspace.storage.fs import FilesystemWorkspace

   workspace = FilesystemWorkspace(use_uuid=True)

   schema = builder.run(
       workspace=workspace,
       copy_images=True  # Copies images to workspace/input/images/
   )

   # Images now include workspace_path
   for img in schema["images"]:
       print(f"Original: {img['path']}")
       print(f"Workspace: {img['workspace_path']}")

Workspace Management
--------------------

The workspace provides organized storage for images.

Directory Structure
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   workspace/
   ├── default/  (or UUID if use_uuid=True)
   │   ├── input/
   │   │   ├── docx/
   │   │   ├── images/          # Extracted images
   │   │   │   ├── img001_img_1.png
   │   │   │   └── img002_img_2.jpg
   │   │   ├── plaintext/
   │   │   └── unzipped/
   │   └── output/
   │       ├── configs/
   │       ├── docx/
   │       └── plaintext/        # Generated plaintext

Copying Images
~~~~~~~~~~~~~~

.. code-block:: python

   workspace = FilesystemWorkspace(root_dir="./workspace")

   # Copy single image
   copied_path = workspace.copy_image(
       src_path="/path/to/source.png",
       image_id="logo",
       index=1  # Optional: creates img001_logo.png
   )

   # Without index: creates logo.png
   copied_path = workspace.copy_image(
       src_path="/path/to/source.png",
       image_id="logo"
   )

Accessing Image Directory
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get image directory path
   image_dir = workspace.directory("input_images")

   # List all images
   from pathlib import Path
   images = list(Path(image_dir).glob("*.png"))

Round-Trip Workflows
--------------------

Complete workflow: extract images from DOCX, generate plaintext, then render back.

Full Example
~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder
   from glyph.core.workspace.storage.fs import FilesystemWorkspace
   from glyph.runner import schema_to_plaintext
   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Step 1: Setup workspace
   workspace = FilesystemWorkspace(root_dir="./workspace", use_uuid=True)

   # Step 2: Extract DOCX (unzip first)
   # unzip source.docx -d extracted/

   # Step 3: Build schema with image extraction
   builder = GlyphSchemaBuilder(
       document_xml_path="extracted/word/document.xml",
       docx_extract_dir="extracted",
       tag="project_v1"
   )

   schema = builder.run(workspace=workspace, copy_images=True)

   print(f"Extracted {len(schema['images'])} images")

   # Step 4: Generate plaintext with image references
   plaintext_path = schema_to_plaintext(
       schema,
       output_path=workspace.directory("output_plaintext") + "/output.glyph.txt"
   )

   print(f"Generated plaintext: {plaintext_path}")

   # Step 5: Create image registry from extracted images
   registry = ImageRegistry()
   for img in schema["images"]:
       registry.register(img["id"], img["workspace_path"])

   # Step 6: Render plaintext back to DOCX
   with open(plaintext_path) as f:
       markup = f.read()

   output_docx = render_markup_to_docx(
       markup,
       output_path=workspace.directory("output_docx") + "/reconstructed.docx",
       image_registry=registry
   )

   print(f"Generated DOCX: {output_docx}")

Editing Workflow
~~~~~~~~~~~~~~~~

Extract, edit plaintext, then render:

.. code-block:: python

   # 1. Extract to plaintext (as above)
   schema = builder.run(workspace=workspace, copy_images=True)
   plaintext = schema_to_plaintext(schema, output_path="editable.glyph.txt")

   # 2. User edits editable.glyph.txt
   #    - Modify text content
   #    - Adjust image sizes
   #    - Change image alignment
   #    - Add/remove images

   # 3. Render edited markup
   registry = ImageRegistry()
   for img in schema["images"]:
       registry.register(img["id"], img["workspace_path"])

   with open("editable.glyph.txt") as f:
       edited_markup = f.read()

   render_markup_to_docx(
       edited_markup,
       output_path="final.docx",
       image_registry=registry
   )

Advanced Usage
--------------

Custom Image Processing
~~~~~~~~~~~~~~~~~~~~~~~

Process images before rendering:

.. code-block:: python

   from PIL import Image
   import os

   def resize_image(src_path, max_width=800):
       """Resize image to max width while preserving aspect ratio."""
       img = Image.open(src_path)

       if img.width > max_width:
           ratio = max_width / img.width
           new_height = int(img.height * ratio)
           img = img.resize((max_width, new_height), Image.LANCZOS)

           # Save resized
           resized_path = src_path.replace(".png", "_resized.png")
           img.save(resized_path)
           return resized_path

       return src_path

   # Use in workflow
   registry = ImageRegistry()
   for img in schema["images"]:
       resized_path = resize_image(img["workspace_path"])
       registry.register(img["id"], resized_path)

Dynamic Image Generation
~~~~~~~~~~~~~~~~~~~~~~~~~

Generate images programmatically:

.. code-block:: python

   import matplotlib.pyplot as plt

   def generate_chart(data, output_path):
       """Generate a chart from data."""
       plt.figure(figsize=(5, 3))
       plt.bar(data.keys(), data.values())
       plt.title("Sales by Region")
       plt.savefig(output_path, dpi=300, bbox_inches='tight')
       plt.close()

   # Generate and register
   chart_path = "/tmp/sales_chart.png"
   generate_chart({"North": 100, "South": 150, "East": 120, "West": 180}, chart_path)

   registry = ImageRegistry()
   registry.register("sales_chart", chart_path)

   # Use in markup
   markup = """
   $glyph-image-id-sales_chart-image-width-5in-image-align-center
   Figure 1: Regional Sales
   $glyph
   """

Image Format Support
~~~~~~~~~~~~~~~~~~~~

Supported formats:

* PNG (.png)
* JPEG (.jpg, .jpeg)
* GIF (.gif)
* BMP (.bmp)
* TIFF (.tiff, .tif)

**Note:** python-docx requires the image file to be accessible at render time.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"Image not found in registry"**

Ensure the image ID matches exactly:

.. code-block:: python

   # Markup uses: image-id-logo
   # Registry must have:
   registry.register("logo", "/path/to/logo.png")  # ✓ Correct

**"FileNotFoundError: image file not found"**

Verify the image path exists:

.. code-block:: python

   import os
   path = "/path/to/image.png"
   if not os.path.exists(path):
       print(f"Image not found: {path}")

**Images appear too large/small**

Specify explicit dimensions:

.. code-block:: text

   $glyph-image-id-logo-image-width-2in-image-height-1.5in
   $glyph

**Images not extracted from DOCX**

Ensure extract directory is provided:

.. code-block:: python

   builder = GlyphSchemaBuilder(
       document_xml_path="document.xml",
       docx_extract_dir="extracted/"  # Required!
   )

Best Practices
--------------

1. **Use consistent image IDs**: Prefer descriptive names (``logo``, ``chart_q4``) over generic ones (``img1``, ``img2``)

2. **Specify dimensions**: Always provide width/height for consistent rendering

3. **Organize images**: Use workspace for automatic organization

4. **Optimize image sizes**: Resize images before adding to documents to reduce file size

5. **Provide alt text**: Include ``image-alt`` for accessibility

6. **Use captions**: Add ``image-caption-below`` for figures and charts

7. **Version control**: Store image registry configuration in code:

   .. code-block:: python

      # config.py
      IMAGE_PATHS = {
          "logo": "assets/logo.png",
          "banner": "assets/banner.jpg",
      }

      # main.py
      registry = ImageRegistry(images=IMAGE_PATHS)

Performance Tips
----------------

* **Batch processing**: Register all images before rendering
* **Cache resized images**: Avoid re-processing images on each render
* **Use appropriate formats**: PNG for logos/screenshots, JPEG for photos
* **Optimize images**: Compress images before adding to registry
