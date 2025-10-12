ForgeClient API
===============

The ``ForgeClient`` class is the main interface for interacting with the Glyph Forge API.

.. currentmodule:: glyph_forge.core.client.forge_client

.. autoclass:: ForgeClient
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__, __enter__, __exit__

Core Methods
------------

Schema Building
~~~~~~~~~~~~~~~

.. automethod:: ForgeClient.build_schema_from_docx

Schema Running
~~~~~~~~~~~~~~

.. automethod:: ForgeClient.run_schema

Bulk Processing
~~~~~~~~~~~~~~~

.. automethod:: ForgeClient.run_schema_bulk

Schema Compression
~~~~~~~~~~~~~~~~~~

.. automethod:: ForgeClient.compress_schema

Plaintext Intake
~~~~~~~~~~~~~~~~

.. automethod:: ForgeClient.intake_plaintext_text
.. automethod:: ForgeClient.intake_plaintext_file

Client Management
~~~~~~~~~~~~~~~~~

.. automethod:: ForgeClient.close


Usage Examples
--------------

Basic Schema Build and Run
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   # Initialize
   client = ForgeClient(api_key="gf_live_...")
   ws = create_workspace()

   # Build schema
   schema = client.build_schema_from_docx(
       ws,
       docx_path="template.docx",
       save_as="my_schema"
   )

   # Run schema
   output = client.run_schema(
       ws,
       schema=schema,
       plaintext="Content here...",
       dest_name="output.docx"
   )

With Context Manager
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   ws = create_workspace()

   with ForgeClient(api_key="gf_live_...") as client:
       schema = client.build_schema_from_docx(
           ws,
           docx_path="template.docx"
       )

Bulk Processing
~~~~~~~~~~~~~~~

.. code-block:: python

   # Process multiple documents at once
   plaintexts = ["Text 1...", "Text 2...", "Text 3..."]

   result = client.run_schema_bulk(
       ws,
       schema=schema,
       plaintexts=plaintexts,
       max_concurrent=5,
       dest_name_pattern="output_{index}.docx"
   )

   print(f"Processed {result['successful']} of {result['total']}")

Schema Compression
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Compress schema to optimize size
   result = client.compress_schema(
       ws,
       schema=schema,
       save_as="compressed_schema"
   )

   print(f"Reduced from {result['stats']['original_count']} "
         f"to {result['stats']['compressed_count']} pattern descriptors")
