Quick Start Guide
=================

This guide will help you get started with Glyph Forge in just a few minutes.

Prerequisites
-------------

Before you begin, ensure you have:

1. Python 3.9+ installed
2. Glyph Forge installed (``pip install glyph-forge``)
3. A Glyph Forge API key (sign up at `glyphapi.ai <https://glyphapi.ai>`_)

Basic Workflow
--------------

The typical Glyph Forge workflow involves three steps:

1. **Build a schema** from a DOCX template
2. **Run the schema** with plaintext to generate documents
3. **Manage outputs** using the workspace system

Step 1: Initialize Client and Workspace
----------------------------------------

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   # Set up API client
   client = ForgeClient(api_key="gf_live_your_api_key")

   # Create workspace for organizing files
   ws = create_workspace()

Step 2: Build a Schema
-----------------------

A schema captures the structure and styling of your DOCX template:

.. code-block:: python

   # Build schema from template DOCX
   schema = client.build_schema_from_docx(
       ws,
       docx_path="templates/resume.docx",
       save_as="resume_schema",
       include_artifacts=False  # Set True for debugging
   )

   print(f"Schema built with {len(schema['pattern_descriptors'])} patterns")

Step 3: Generate Documents
---------------------------

Use the schema to generate new documents from plaintext:

.. code-block:: python

   # Read plaintext content
   with open("content.txt", "r") as f:
       plaintext = f.read()

   # Generate DOCX from schema + plaintext
   output_path = client.run_schema(
       ws,
       schema=schema,
       plaintext=plaintext,
       dest_name="generated_resume.docx"
   )

   print(f"Document generated: {output_path}")

Complete Example
----------------

Here's a complete end-to-end example:

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace
   import os

   # Initialize
   api_key = os.getenv("GLYPH_API_KEY")  # Or pass directly
   client = ForgeClient(api_key=api_key)
   ws = create_workspace()

   try:
       # Build schema
       schema = client.build_schema_from_docx(
           ws,
           docx_path="template.docx",
           save_as="my_schema"
       )

       # Generate document
       output = client.run_schema(
           ws,
           schema=schema,
           plaintext="This is my content...",
           dest_name="output.docx"
       )

       print(f"Success! Document saved to: {output}")

   finally:
       client.close()

Using Context Manager
---------------------

For automatic resource cleanup, use the context manager:

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   ws = create_workspace()

   with ForgeClient(api_key="gf_live_...") as client:
       schema = client.build_schema_from_docx(ws, docx_path="template.docx")
       output = client.run_schema(ws, schema=schema, plaintext="Content...")

   # Client is automatically closed

Next Steps
----------

- Learn about :doc:`authentication` options
- Explore :doc:`workspace` management features
- Check out the :doc:`../examples/basic_usage` examples
- Review the :doc:`../api/client` API reference
