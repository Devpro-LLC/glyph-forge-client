Image Workflow Examples
=======================

This guide provides practical examples for working with images in the Glyph SDK.

Basic Image Rendering
----------------------

Simple Image Insertion
~~~~~~~~~~~~~~~~~~~~~~

Insert an image with basic sizing:

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Register images
   registry = ImageRegistry()
   registry.register("logo", "assets/company_logo.png")

   # Create markup
   markup = """
   $glyph-bold-font-size-24-align-center
   Company Annual Report
   $glyph

   $glyph-image-id-logo-image-width-2in-image-align-center
   $glyph

   $glyph-align-center
   Fiscal Year 2025
   $glyph
   """

   # Render
   render_markup_to_docx(markup, output_path="report.docx", image_registry=registry)

Multiple Images
~~~~~~~~~~~~~~~

Include several images in a document:

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Register multiple images
   registry = ImageRegistry()
   registry.register("chart1", "charts/revenue_chart.png")
   registry.register("chart2", "charts/expenses_chart.png")
   registry.register("chart3", "charts/profit_chart.png")

   markup = """
   $glyph-bold-font-size-18
   Financial Overview
   $glyph

   $glyph-image-id-chart1-image-width-5in-image-height-3in-image-align-center
   Figure 1: Revenue Growth
   $glyph

   Our revenue increased by 25% year-over-year.

   $glyph-image-id-chart2-image-width-5in-image-height-3in-image-align-center
   Figure 2: Expense Breakdown
   $glyph

   Operating expenses were well-controlled.

   $glyph-image-id-chart3-image-width-5in-image-height-3in-image-align-center
   Figure 3: Net Profit Margin
   $glyph

   We achieved record profitability this year.
   """

   render_markup_to_docx(markup, output_path="financial_report.docx", image_registry=registry)

Images with Captions
~~~~~~~~~~~~~~~~~~~~

Add descriptive captions to images:

.. code-block:: python

   registry = ImageRegistry()
   registry.register("diagram", "assets/architecture_diagram.png")

   markup = """
   $glyph-bold-font-size-18
   System Architecture
   $glyph

   The following diagram shows our microservices architecture:

   $glyph-image-id-diagram-image-width-6in-image-align-center-image-caption-below
   Figure 1: Microservices Architecture showing API Gateway, Auth Service, and Data Layer
   $glyph

   $glyph-italic
   Note: All services communicate via REST APIs with JWT authentication.
   $glyph
   """

   render_markup_to_docx(markup, output_path="architecture.docx", image_registry=registry)

Image Extraction
----------------

Extract from DOCX
~~~~~~~~~~~~~~~~~

Extract images and metadata from an existing DOCX file:

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder
   from glyph.core.workspace.storage.fs import FilesystemWorkspace
   from zipfile import ZipFile

   # Extract DOCX
   with ZipFile("source.docx", 'r') as zip_ref:
       zip_ref.extractall("extracted/")

   # Create workspace
   workspace = FilesystemWorkspace(root_dir="./workspace", use_uuid=True)

   # Build schema with image extraction
   builder = GlyphSchemaBuilder(
       document_xml_path="extracted/word/document.xml",
       docx_extract_dir="extracted",
       tag="project_alpha"
   )

   schema = builder.run(workspace=workspace, copy_images=True)

   # Inspect extracted images
   print(f"Found {len(schema['images'])} images:\n")

   for img in schema["images"]:
       print(f"ID: {img['id']}")
       print(f"  Name: {img['name']}")
       print(f"  Size: {img['width_inches']:.2f} x {img['height_inches']:.2f} inches")
       print(f"  Path: {img['workspace_path']}")
       print(f"  Alt text: {img['alt_text']}")
       print()

Process Extracted Images
~~~~~~~~~~~~~~~~~~~~~~~~~

Modify extracted images before rendering:

.. code-block:: python

   from PIL import Image
   from glyph.core.markup.engine.integration import ImageRegistry

   # Extract images (as above)
   schema = builder.run(workspace=workspace, copy_images=True)

   # Process images
   registry = ImageRegistry()

   for img in schema["images"]:
       # Open and process
       pil_image = Image.open(img["workspace_path"])

       # Convert to grayscale
       grayscale = pil_image.convert('L')

       # Save processed version
       processed_path = img["workspace_path"].replace(".png", "_gray.png")
       grayscale.save(processed_path)

       # Register processed image
       registry.register(img["id"], processed_path)

   # Use in markup...

Round-Trip Workflows
--------------------

Complete DOCX Round-Trip
~~~~~~~~~~~~~~~~~~~~~~~~

Extract from DOCX, generate plaintext, edit, and render back:

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder
   from glyph.core.workspace.storage.fs import FilesystemWorkspace
   from glyph.runner import schema_to_plaintext
   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry
   from zipfile import ZipFile
   from pathlib import Path

   # 1. Extract source DOCX
   source_docx = "source_template.docx"
   extract_dir = "extracted/"

   with ZipFile(source_docx, 'r') as zip_ref:
       zip_ref.extractall(extract_dir)

   # 2. Create workspace
   workspace = FilesystemWorkspace(root_dir="./workspace", use_uuid=True)

   # 3. Build schema with images
   builder = GlyphSchemaBuilder(
       document_xml_path=f"{extract_dir}/word/document.xml",
       docx_extract_dir=extract_dir,
       source_docx=source_docx,
       tag="template_v1"
   )

   schema = builder.run(workspace=workspace, copy_images=True)

   print(f"✓ Extracted {len(schema['images'])} images")
   print(f"✓ Analyzed {len(schema['pattern_descriptors'])} paragraphs")

   # 4. Generate editable plaintext
   plaintext_path = Path(workspace.directory("output_plaintext")) / "editable.glyph.txt"
   plaintext = schema_to_plaintext(schema, output_path=str(plaintext_path))

   print(f"✓ Generated plaintext: {plaintext_path}")
   print("\nYou can now edit the plaintext file.")
   print("Example edits:")
   print("  - Change text content")
   print("  - Adjust image sizes (image-width-4in → image-width-5in)")
   print("  - Change alignment (image-align-left → image-align-center)")
   print("\nPress Enter when ready to render...")
   input()

   # 5. Create image registry
   registry = ImageRegistry()
   for img in schema["images"]:
       registry.register(img["id"], img["workspace_path"])

   # 6. Render edited plaintext to DOCX
   with open(plaintext_path) as f:
       edited_markup = f.read()

   output_path = Path(workspace.directory("output_docx")) / "final.docx"
   render_markup_to_docx(
       edited_markup,
       output_path=str(output_path),
       image_registry=registry,
       validate=False  # Skip validation for schema-generated markup
   )

   print(f"✓ Generated final DOCX: {output_path}")

Template-Based Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use extracted schema as a template for multiple documents:

.. code-block:: python

   # Extract template schema once
   template_schema = builder.run(workspace=workspace, copy_images=True)

   # Create registry from template
   base_registry = ImageRegistry()
   for img in template_schema["images"]:
       base_registry.register(img["id"], img["workspace_path"])

   # Generate multiple documents with different content
   documents = [
       {"title": "Q1 Report", "revenue": 1.2, "chart": "q1_chart.png"},
       {"title": "Q2 Report", "revenue": 1.5, "chart": "q2_chart.png"},
       {"title": "Q3 Report", "revenue": 1.8, "chart": "q3_chart.png"},
       {"title": "Q4 Report", "revenue": 2.1, "chart": "q4_chart.png"},
   ]

   for doc in documents:
       # Clone base registry
       registry = ImageRegistry(images=base_registry.images.copy())

       # Add quarter-specific chart
       registry.register("quarterly_chart", f"charts/{doc['chart']}")

       # Generate markup
       markup = f"""
       $glyph-bold-font-size-24-align-center
       {doc['title']}
       $glyph

       $glyph-image-id-logo-image-width-2in-image-align-center
       $glyph

       $glyph-bold-font-size-18
       Financial Summary
       $glyph

       Revenue: ${doc['revenue']}M

       $glyph-image-id-quarterly_chart-image-width-5in-image-height-3in-image-align-center
       Quarterly Performance
       $glyph
       """

       # Render
       output_file = f"reports/{doc['title'].replace(' ', '_').lower()}.docx"
       render_markup_to_docx(markup, output_path=output_file, image_registry=registry)

       print(f"✓ Generated {output_file}")

Dynamic Image Generation
-------------------------

Generate Charts with Matplotlib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create charts programmatically and include in documents:

.. code-block:: python

   import matplotlib.pyplot as plt
   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Generate revenue chart
   def create_revenue_chart(quarters, revenues, output_path):
       plt.figure(figsize=(6, 4))
       plt.bar(quarters, revenues, color='steelblue')
       plt.xlabel('Quarter')
       plt.ylabel('Revenue ($M)')
       plt.title('Quarterly Revenue')
       plt.grid(axis='y', alpha=0.3)
       plt.tight_layout()
       plt.savefig(output_path, dpi=300, bbox_inches='tight')
       plt.close()

   # Generate profit chart
   def create_profit_chart(quarters, profits, output_path):
       plt.figure(figsize=(6, 4))
       plt.plot(quarters, profits, marker='o', linewidth=2, color='green')
       plt.xlabel('Quarter')
       plt.ylabel('Profit ($M)')
       plt.title('Quarterly Profit Trend')
       plt.grid(True, alpha=0.3)
       plt.tight_layout()
       plt.savefig(output_path, dpi=300, bbox_inches='tight')
       plt.close()

   # Data
   quarters = ['Q1', 'Q2', 'Q3', 'Q4']
   revenues = [1.2, 1.5, 1.8, 2.1]
   profits = [0.3, 0.4, 0.5, 0.7]

   # Generate charts
   revenue_chart = "/tmp/revenue_chart.png"
   profit_chart = "/tmp/profit_chart.png"

   create_revenue_chart(quarters, revenues, revenue_chart)
   create_profit_chart(quarters, profits, profit_chart)

   # Register and render
   registry = ImageRegistry()
   registry.register("revenue", revenue_chart)
   registry.register("profit", profit_chart)

   markup = """
   $glyph-bold-font-size-24-align-center
   2025 Financial Report
   $glyph

   $glyph-bold-font-size-18
   Revenue Analysis
   $glyph

   $glyph-image-id-revenue-image-width-5in-image-align-center
   Figure 1: Quarterly Revenue
   $glyph

   Revenue showed consistent growth throughout the year.

   $glyph-bold-font-size-18
   Profitability
   $glyph

   $glyph-image-id-profit-image-width-5in-image-align-center
   Figure 2: Profit Trend
   $glyph

   Profit margins improved significantly in Q4.
   """

   render_markup_to_docx(markup, output_path="financial_report.docx", image_registry=registry)

QR Code Generation
~~~~~~~~~~~~~~~~~~

Generate and embed QR codes:

.. code-block:: python

   import qrcode
   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   def generate_qr_code(data, output_path):
       qr = qrcode.QRCode(version=1, box_size=10, border=4)
       qr.add_data(data)
       qr.make(fit=True)
       img = qr.make_image(fill_color="black", back_color="white")
       img.save(output_path)

   # Generate QR codes
   website_qr = "/tmp/website_qr.png"
   contact_qr = "/tmp/contact_qr.png"

   generate_qr_code("https://example.com", website_qr)
   generate_qr_code("mailto:contact@example.com", contact_qr)

   # Register and render
   registry = ImageRegistry()
   registry.register("website", website_qr)
   registry.register("contact", contact_qr)

   markup = """
   $glyph-bold-font-size-18-align-center
   Connect With Us
   $glyph

   $glyph-align-center
   Visit our website:
   $glyph

   $glyph-image-id-website-image-width-1.5in-image-align-center
   $glyph

   $glyph-align-center
   Or email us:
   $glyph

   $glyph-image-id-contact-image-width-1.5in-image-align-center
   $glyph
   """

   render_markup_to_docx(markup, output_path="contact_card.docx", image_registry=registry)

Batch Processing
----------------

Process Multiple DOCX Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extract images from multiple documents:

.. code-block:: python

   from pathlib import Path
   from glyph.core.schema import GlyphSchemaBuilder
   from glyph.core.workspace.storage.fs import FilesystemWorkspace
   from zipfile import ZipFile
   import json

   # Create workspace
   workspace = FilesystemWorkspace(root_dir="./batch_workspace", use_uuid=True)

   # Process all DOCX files
   docx_files = Path("templates/").glob("*.docx")
   results = []

   for docx_path in docx_files:
       print(f"Processing {docx_path.name}...")

       # Extract
       extract_dir = f"extracted/{docx_path.stem}"
       with ZipFile(docx_path, 'r') as zip_ref:
           zip_ref.extractall(extract_dir)

       # Build schema
       builder = GlyphSchemaBuilder(
           document_xml_path=f"{extract_dir}/word/document.xml",
           docx_extract_dir=extract_dir,
           tag=docx_path.stem
       )

       schema = builder.run(workspace=workspace, copy_images=True)

       # Save schema
       schema_path = f"schemas/{docx_path.stem}.json"
       Path("schemas").mkdir(exist_ok=True)
       with open(schema_path, 'w') as f:
           json.dump(schema, f, indent=2)

       results.append({
           "file": docx_path.name,
           "images": len(schema["images"]),
           "paragraphs": len(schema["pattern_descriptors"]),
           "schema_path": schema_path
       })

       print(f"  ✓ Extracted {len(schema['images'])} images")

   # Summary
   print("\nBatch Processing Summary:")
   print(f"Processed {len(results)} documents")
   print(f"Total images: {sum(r['images'] for r in results)}")
   for r in results:
       print(f"  {r['file']}: {r['images']} images → {r['schema_path']}")

Bulk Image Optimization
~~~~~~~~~~~~~~~~~~~~~~~

Optimize images for all documents:

.. code-block:: python

   from PIL import Image
   from pathlib import Path

   def optimize_image(src_path, max_width=1200, quality=85):
       """Optimize image size and quality."""
       img = Image.open(src_path)

       # Resize if too large
       if img.width > max_width:
           ratio = max_width / img.width
           new_height = int(img.height * ratio)
           img = img.resize((max_width, new_height), Image.LANCZOS)

       # Optimize
       optimized_path = src_path.replace(".png", "_opt.png")

       if src_path.endswith('.png'):
           img.save(optimized_path, "PNG", optimize=True)
       elif src_path.endswith(('.jpg', '.jpeg')):
           img.save(optimized_path.replace('.png', '.jpg'), "JPEG", quality=quality, optimize=True)

       return optimized_path

   # Process all workspace images
   image_dir = Path(workspace.directory("input_images"))

   for img_file in image_dir.glob("*.png"):
       optimized = optimize_image(str(img_file))
       original_size = img_file.stat().st_size
       optimized_size = Path(optimized).stat().st_size
       savings = (1 - optimized_size / original_size) * 100

       print(f"{img_file.name}: {original_size:,} → {optimized_size:,} bytes ({savings:.1f}% reduction)")
