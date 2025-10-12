Installation
============

Requirements
------------

- Python 3.9 or higher
- pip package manager

Install from PyPI
-----------------

The recommended way to install Glyph Forge is via pip:

.. code-block:: bash

   pip install glyph-forge

This will install the latest stable version from PyPI.

Install Development Version
----------------------------

To install the latest development version from GitHub:

.. code-block:: bash

   pip install git+https://github.com/Devpro-LLC/glyph-forge-client.git

Install with Optional Dependencies
-----------------------------------

For testing:

.. code-block:: bash

   pip install glyph-forge[test]

For documentation:

.. code-block:: bash

   pip install glyph-forge[docs]

All optional dependencies:

.. code-block:: bash

   pip install glyph-forge[test,docs]

Verify Installation
-------------------

Verify the installation by checking the version:

.. code-block:: python

   import glyph_forge
   print(glyph_forge.__version__)

Or from the command line:

.. code-block:: bash

   python -c "import glyph_forge; print(glyph_forge.__version__)"

Next Steps
----------

After installation, proceed to the :doc:`quickstart` guide to learn how to use Glyph Forge.
