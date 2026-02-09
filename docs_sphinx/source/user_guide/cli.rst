Command Line Interface
======================

The Glyph SDK provides a command-line interface for building schemas and running schema-based document generation workflows.

Installation
------------

The CLI is included when you install the SDK:

.. code-block:: bash

   pip install glyph-forge

Commands
--------

build_schema
~~~~~~~~~~~~

Build a schema from a DOCX document.xml file.

**Usage:**

.. code-block:: bash

   python -m glyph.runner --document path/to/document.xml \
                          --extract path/to/extracted_docx \
                          --output schema.json

**Arguments:**

* ``--document, -d`` **(required)**: Path to document.xml file
* ``--extract, -e`` **(optional)**: Path to extracted DOCX folder (enables full feature extraction)
* ``--output, -o`` **(optional)**: Output JSON file path (default: stdout)

**Example:**

.. code-block:: bash

   # Extract DOCX first
   unzip template.docx -d extracted/

   # Build schema
   python -m glyph.runner --document extracted/word/document.xml \
                          --extract extracted \
                          --output my_schema.json

**Output:**

The schema JSON includes:

* ``pattern_descriptors``: Classification and styling for each paragraph
* ``images``: Extracted image metadata (when --extract provided)
* ``global_defaults``: Document-level settings (page size, margins, fonts)
* ``headers/footers``: Header and footer content
* ``theme``: Color scheme and theme information

schema_to_plaintext
~~~~~~~~~~~~~~~~~~~

Generate Glyph markup plaintext from a schema.

**Python API:**

.. code-block:: python

   from glyph.runner import schema_to_plaintext

   # From schema dict
   schema = build_schema("document.xml", "extract_dir")
   plaintext = schema_to_plaintext(schema, output_path="output.glyph.txt")

   # From schema JSON file
   plaintext = schema_to_plaintext("schema.json", output_path="output.glyph.txt")

**What it does:**

1. Converts pattern descriptors to Glyph markup syntax
2. Includes image references using ``$glyph-image-id-{key}`` syntax
3. Preserves document structure and styling
4. Creates a round-trippable plaintext representation

run_schema
~~~~~~~~~~

Run a schema to generate a DOCX document.

**Python API:**

.. code-block:: python

   from glyph.runner import run_schema

   run_schema(
       schema_path="schema.json",
       output_path="output.docx",
       source_override="template.docx"  # Optional
   )

**Arguments:**

* ``schema_path``: Path to schema JSON file
* ``output_path``: Output DOCX file path (optional, prints debug if not provided)
* ``source_override``: Override source DOCX path from schema (optional)

index
~~~~~

Build a structured document index with heading-bounded sections and optional form-annotated segments.

**Usage:**

.. code-block:: bash

   glyph-forge index <input> [--section-forms FORMS] [--annotate-forms FORMS]
                              [--threshold N] [--no-context] [-o DIR] [-v]

**Arguments:**

* ``input`` **(required)**: Path to input file (``.docx`` or plaintext)
* ``--section-forms``: Comma-separated heading forms for section boundaries (e.g. ``H-SHORT,H-SECTION-N``). Default: all heading forms.
* ``--annotate-forms``: Comma-separated form codes to annotate as segments (e.g. ``L-BULLET,T-ROW``). Default: none (segments skipped for performance).
* ``--threshold``: Minimum confidence threshold (default: 0.55)
* ``--no-context``: Disable surrounding-line context for classification
* ``-v, --verbose``: Show per-section segment details

**Examples:**

.. code-block:: bash

   # Index a plaintext file (section structure only)
   glyph-forge index report.txt

   # Index with bullet and table annotations
   glyph-forge index report.txt --annotate-forms L-BULLET,T-ROW

   # Index a DOCX file (auto-detected by extension)
   glyph-forge index report.docx

   # Only split on short headings and numbered sections
   glyph-forge index report.txt --section-forms H-SHORT,H-SECTION-N

   # Verbose output with segment details
   glyph-forge index report.txt --annotate-forms L-BULLET -v

**Output:**

The command prints a summary table of sections with their heading form, score, line count, and number of segments. With ``-v``, each section's segments are listed with their form type, line range, and a content preview.


Workflow Examples
-----------------

Complete Round-Trip
~~~~~~~~~~~~~~~~~~~

Extract schema from DOCX, generate plaintext, then reconstruct:

.. code-block:: bash

   # 1. Extract DOCX
   unzip source.docx -d extracted/

   # 2. Build schema
   python -m glyph.runner -d extracted/word/document.xml \
                          -e extracted \
                          -o schema.json

   # 3. Generate plaintext (Python)
   python -c "from glyph.runner import schema_to_plaintext; \
              schema_to_plaintext('schema.json', 'output.glyph.txt')"

   # 4. Edit plaintext as needed, then render (Python)
   python -c "from glyph.core.markup.engine.integration import render_markup_to_docx; \
              render_markup_to_docx(open('output.glyph.txt').read(), output_path='final.docx')"

Batch Processing
~~~~~~~~~~~~~~~~

Process multiple documents:

.. code-block:: python

   from glyph.runner import build_schema, schema_to_plaintext
   from pathlib import Path

   docx_files = Path("templates/").glob("*.docx")

   for docx_path in docx_files:
       # Extract
       extract_dir = f"extracted/{docx_path.stem}"
       # ... unzip logic ...

       # Build schema
       schema = build_schema(
           f"{extract_dir}/word/document.xml",
           extract_dir,
           source_docx=str(docx_path)
       )

       # Save schema
       import json
       with open(f"schemas/{docx_path.stem}.json", "w") as f:
           json.dump(schema, f, indent=2)

       # Generate plaintext
       schema_to_plaintext(
           schema,
           output_path=f"plaintext/{docx_path.stem}.glyph.txt"
       )

Advanced Options
----------------

Custom Workspace
~~~~~~~~~~~~~~~~

Use a custom workspace for organized file management:

.. code-block:: python

   from glyph.core.workspace.storage.fs import FilesystemWorkspace
   from glyph.core.schema import GlyphSchemaBuilder

   # Create workspace
   ws = FilesystemWorkspace(
       root_dir="./my_workspace",
       use_uuid=True  # Create unique run directories
   )

   # Build schema with workspace
   builder = GlyphSchemaBuilder(
       document_xml_path="extracted/word/document.xml",
       docx_extract_dir="extracted",
       tag="my_project"
   )

   schema = builder.run(
       workspace=ws,
       copy_images=True  # Copy images to workspace
   )

   # Images are now in: ws.directory("input_images")

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

Set default paths and options:

.. code-block:: bash

   export GLYPH_WORKSPACE_DIR="$HOME/.glyph/workspace"
   export GLYPH_DEFAULT_TAG="production"

Debugging
---------

Enable verbose output:

.. code-block:: python

   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Now all Glyph operations will show debug output

Check schema validity:

.. code-block:: python

   from glyph.core.schema import compress_schema, get_compression_stats

   # Load schema
   import json
   schema = json.load(open("schema.json"))

   # Compress and get stats
   compressed = compress_schema(schema)
   stats = get_compression_stats(schema, compressed)

   print(f"Original descriptors: {stats['original_count']}")
   print(f"Compressed descriptors: {stats['compressed_count']}")
   print(f"Compression ratio: {stats['compression_ratio']:.2%}")

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"FileNotFoundError: document.xml not found"**

Ensure you've extracted the DOCX first:

.. code-block:: bash

   unzip template.docx -d extracted/

**"Schema missing 'source_docx'"**

When running a schema, provide the source DOCX:

.. code-block:: python

   run_schema("schema.json", output_path="out.docx", source_override="template.docx")

**"Images not found in output"**

Ensure you provide the extract directory when building:

.. code-block:: bash

   python -m glyph.runner -d extracted/word/document.xml -e extracted

For image rendering, use ImageRegistry:

.. code-block:: python

   from glyph.core.markup.engine.integration import ImageRegistry

   registry = ImageRegistry()
   registry.register("img_1", "path/to/image.png")
