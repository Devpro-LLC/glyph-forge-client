Exceptions
==========

Glyph Forge provides a hierarchy of exceptions for error handling.

.. currentmodule:: glyph_forge.core.client.exceptions

Exception Hierarchy
-------------------

.. autoexception:: ForgeClientError
   :members:
   :show-inheritance:

.. autoexception:: ForgeClientHTTPError
   :members:
   :show-inheritance:

.. autoexception:: ForgeClientIOError
   :members:
   :show-inheritance:

Usage Examples
--------------

Basic Error Handling
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace
   from glyph_forge.core.client.exceptions import (
       ForgeClientError,
       ForgeClientHTTPError,
       ForgeClientIOError
   )

   client = ForgeClient(api_key="gf_live_...")
   ws = create_workspace()

   try:
       schema = client.build_schema_from_docx(
           ws,
           docx_path="template.docx"
       )
   except ForgeClientHTTPError as e:
       print(f"HTTP Error {e.status_code}: {e.message}")
       print(f"Response: {e.response_body}")
   except ForgeClientIOError as e:
       print(f"Network Error: {e.message}")
   except ForgeClientError as e:
       print(f"Client Error: {e.message}")

Handling Rate Limits
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge.core.client.exceptions import ForgeClientHTTPError

   try:
       result = client.run_schema(ws, schema=schema, plaintext=text)
   except ForgeClientHTTPError as e:
       if e.status_code == 429:
           print("Rate limit exceeded, please wait...")
           print(f"Rate limit info: {client.last_rate_limit_info}")
       else:
           raise
