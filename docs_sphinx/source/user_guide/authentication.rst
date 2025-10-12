Authentication
==============

Glyph Forge uses API keys for authentication. This guide covers how to obtain and use API keys.

Getting an API Key
------------------

1. Sign up at `glyphapi.ai <https://glyphapi.ai>`_
2. Navigate to your account settings
3. Generate a new API key
4. Copy the key (it starts with ``gf_live_`` or ``gf_test_``)

API Key Types
-------------

- **Live Keys** (``gf_live_...``): For production use
- **Test Keys** (``gf_test_...``): For development and testing

Using API Keys
--------------

Method 1: Direct Parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass the API key directly to the client:

.. code-block:: python

   from glyph_forge import ForgeClient

   client = ForgeClient(api_key="gf_live_your_key_here")

Method 2: Environment Variable
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set the ``GLYPH_API_KEY`` environment variable:

.. code-block:: bash

   export GLYPH_API_KEY="gf_live_your_key_here"

Then initialize the client without explicitly passing the key:

.. code-block:: python

   from glyph_forge import ForgeClient

   # Automatically reads from GLYPH_API_KEY env var
   client = ForgeClient()

Method 3: .env File
~~~~~~~~~~~~~~~~~~~

Use a ``.env`` file for managing environment variables:

.. code-block:: text

   # .env file
   GLYPH_API_KEY=gf_live_your_key_here
   GLYPH_API_BASE=https://api.glyphapi.ai

Load it with python-dotenv:

.. code-block:: python

   from dotenv import load_dotenv
   from glyph_forge import ForgeClient

   load_dotenv()  # Load .env file
   client = ForgeClient()  # Uses env var

Custom Base URL
---------------

For self-hosted or regional deployments, specify a custom base URL:

.. code-block:: python

   client = ForgeClient(
       api_key="gf_live_...",
       base_url="https://api.glyphapi.ai"
   )

Or via environment variable:

.. code-block:: bash

   export GLYPH_API_BASE="https://api.glyphapi.ai"

Security Best Practices
-----------------------

1. **Never commit API keys to version control**

   Add ``.env`` to your ``.gitignore``:

   .. code-block:: text

      # .gitignore
      .env
      *.key

2. **Use environment variables in production**

   Set environment variables through your deployment platform (Heroku, AWS, etc.)

3. **Rotate keys regularly**

   Generate new keys periodically and revoke old ones

4. **Use test keys for development**

   Keep live keys separate from test keys

5. **Limit key permissions**

   Use different keys for different applications or teams

Rate Limiting
-------------

API keys are subject to rate limits based on your subscription tier. The client automatically includes rate limit information in responses:

.. code-block:: python

   from glyph_forge import ForgeClient

   client = ForgeClient(api_key="gf_live_...")

   # Make a request
   schema = client.build_schema_from_docx(ws, docx_path="template.docx")

   # Check rate limit status
   if client.last_rate_limit_info:
       print(f"Tier: {client.last_rate_limit_info['X-Subscription-Tier']}")
       print(f"Remaining: {client.last_rate_limit_info['X-Requests-Remaining']}")

Error Handling
--------------

Handle authentication errors gracefully:

.. code-block:: python

   from glyph_forge import ForgeClient
   from glyph_forge.core.client.exceptions import ForgeClientHTTPError

   try:
       client = ForgeClient(api_key="invalid_key")
       schema = client.build_schema_from_docx(ws, docx_path="template.docx")
   except ForgeClientHTTPError as e:
       if e.status_code == 401:
           print("Invalid API key")
       elif e.status_code == 403:
           print("Account inactive or no subscription")
       elif e.status_code == 429:
           print("Rate limit exceeded")
       else:
           print(f"HTTP Error: {e}")
