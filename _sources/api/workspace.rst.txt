Workspace API
=============

The workspace system provides organized storage for inputs, outputs, and artifacts.

.. currentmodule:: glyph_forge.core.workspace

Creating a Workspace
--------------------

.. autofunction:: glyph_forge.create_workspace

Workspace Class
---------------

.. autoclass:: glyph_forge.core.workspace.workspace.Workspace
   :members:
   :undoc-members:
   :show-inheritance:

Usage Examples
--------------

Basic Workspace Creation
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import create_workspace

   # Create workspace in current directory
   ws = create_workspace()

   # Create workspace in specific directory
   ws = create_workspace(root_dir="/path/to/workspace")

   # Create workspace without UUID suffix
   ws = create_workspace(use_uuid=False)

Working with Directories
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get directory paths
   input_dir = ws.directory("input_docx")
   output_dir = ws.directory("output_docx")
   config_dir = ws.directory("output_configs")

   # List files in directory
   files = ws.list_files("output_docx", pattern="*.docx")

Saving and Loading Data
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Save JSON data
   schema_path = ws.save_json("output_configs", "my_schema", schema_dict)

   # Load JSON data
   schema = ws.load_json("output_configs", "my_schema")

   # Save binary data
   ws.save_binary("output_docx", "output.docx", docx_bytes)
