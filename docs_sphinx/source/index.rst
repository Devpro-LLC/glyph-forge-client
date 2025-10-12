Glyph Forge Documentation
==========================

**Glyph Forge** is a powerful Python client for the Glyph Forge API that enables document generation, schema building, and plaintext processing workflows.

.. image:: https://img.shields.io/pypi/v/glyph-forge.svg
   :target: https://pypi.org/project/glyph-forge/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/glyph-forge.svg
   :target: https://pypi.org/project/glyph-forge/
   :alt: Python versions

.. image:: https://img.shields.io/github/license/Devpro-LLC/glyph-forge-client.svg
   :target: https://github.com/Devpro-LLC/glyph-forge-client/blob/main/LICENSE
   :alt: License


Features
--------

- **Schema Building**: Build schemas from DOCX templates
- **Schema Running**: Generate documents from schemas and plaintext
- **Bulk Processing**: Process multiple documents in parallel
- **Schema Compression**: Optimize schemas by deduplicating pattern descriptors
- **Plaintext Processing**: Intake and normalize plaintext content
- **Workspace Management**: Organize inputs, outputs, and artifacts
- **Type Safety**: Full type hints for better IDE support
- **Error Handling**: Comprehensive exception handling with detailed error messages


Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

   pip install glyph-forge

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   # Initialize client and workspace
   client = ForgeClient(api_key="your_api_key")
   ws = create_workspace()

   # Build schema from DOCX
   schema = client.build_schema_from_docx(
       ws,
       docx_path="template.docx",
       save_as="my_schema"
   )

   # Run schema with plaintext
   output_path = client.run_schema(
       ws,
       schema=schema,
       plaintext="Your content here...",
       dest_name="output.docx"
   )

   print(f"Generated document: {output_path}")


Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/installation
   user_guide/quickstart
   user_guide/authentication
   user_guide/workspace

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/client
   api/workspace
   api/exceptions

.. toctree::
   :maxdepth: 2
   :caption: Examples

   examples/basic_usage
   examples/bulk_processing
   examples/compression
   examples/advanced

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   contributing
   license


Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

