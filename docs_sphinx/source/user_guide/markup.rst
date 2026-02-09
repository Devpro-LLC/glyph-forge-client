Glyph Markup Language
=====================

The Glyph markup language is a lightweight syntax for defining document structure and styling in plaintext format. It provides a human-readable way to specify formatting that can be rendered to DOCX.

Overview
--------

Glyph markup uses a block-based syntax with utility classes:

.. code-block:: text

   $glyph-utility-class1-utility-class2
   Content goes here
   $glyph

   Plain text without formatting appears as-is.

Key Features
~~~~~~~~~~~~

* **Block-based structure**: Content wrapped in ``$glyph`` blocks
* **Utility classes**: Chainable classes for styling (e.g., ``bold-italic-align-center``)
* **Plain text support**: Text outside blocks renders as normal paragraphs
* **Image support**: Inline images with dimensions and alignment
* **Type-safe validation**: Built-in validation catches errors before rendering

Basic Syntax
------------

Block Structure
~~~~~~~~~~~~~~~

A Glyph block consists of:

1. **Opening tag**: ``$glyph-{classes}`` where classes are hyphen-separated
2. **Content**: Text content (can be multi-line)
3. **Closing tag**: ``$glyph``

**Example:**

.. code-block:: text

   $glyph-bold-align-center
   This text is bold and centered
   $glyph

   This is plain text without formatting.

   $glyph-italic
   This text is italic
   $glyph

Plain Text
~~~~~~~~~~

Text outside ``$glyph`` blocks is rendered as normal paragraphs:

.. code-block:: text

   This is a regular paragraph.

   This is another paragraph.

Utility Classes
---------------

Text Formatting
~~~~~~~~~~~~~~~

Apply text styling to runs:

* ``bold`` - Bold text
* ``italic`` - Italic text
* ``underline`` - Underlined text
* ``strikethrough`` - Strikethrough text

**Example:**

.. code-block:: text

   $glyph-bold-italic
   Bold and italic text
   $glyph

Paragraph Alignment
~~~~~~~~~~~~~~~~~~~

Control paragraph alignment:

* ``align-left`` - Left alignment (default)
* ``align-center`` - Center alignment
* ``align-right`` - Right alignment
* ``align-justify`` - Justified alignment

**Example:**

.. code-block:: text

   $glyph-align-center
   This paragraph is centered
   $glyph

Font Properties
~~~~~~~~~~~~~~~

**Font Size:**

.. code-block:: text

   $glyph-font-size-14
   14-point text
   $glyph

   $glyph-font-size-24-bold
   24-point bold text
   $glyph

**Font Color:**

.. code-block:: text

   $glyph-color-FF0000
   Red text (hex color)
   $glyph

   $glyph-color-blue
   Blue text (named color)
   $glyph

**Font Family:**

.. code-block:: text

   $glyph-font-family-Arial
   Arial font
   $glyph

Paragraph Spacing
~~~~~~~~~~~~~~~~~

Control spacing before and after paragraphs:

.. code-block:: text

   $glyph-space-before-12pt
   Paragraph with 12pt space before
   $glyph

   $glyph-space-after-6pt
   Paragraph with 6pt space after
   $glyph

Line Spacing
~~~~~~~~~~~~

Set line height:

.. code-block:: text

   $glyph-line-spacing-1.5
   Paragraph with 1.5 line spacing
   $glyph

   $glyph-line-spacing-double
   Double-spaced paragraph
   $glyph

Indentation
~~~~~~~~~~~

Control paragraph indentation:

.. code-block:: text

   $glyph-indent-left-0.5in
   Indented 0.5 inches from left
   $glyph

   $glyph-indent-first-line-0.25in
   First line indented 0.25 inches
   $glyph

Page Breaks
~~~~~~~~~~~

Insert page breaks:

.. code-block:: text

   $glyph-page-break-before
   This starts on a new page
   $glyph

Image Support
-------------

Inline Images
~~~~~~~~~~~~~

Insert images with dimensions and alignment:

.. code-block:: text

   $glyph-image-id-{key}-image-width-{N}in-image-height-{N}in-image-align-{position}
   Optional caption text
   $glyph

**Image Utilities:**

* ``image-id-{key}`` - Image identifier (required, must be registered)
* ``image-width-{N}in`` - Width in inches (e.g., ``image-width-2in``)
* ``image-height-{N}in`` - Height in inches (e.g., ``image-height-1.5in``)
* ``image-align-left`` - Left-aligned image
* ``image-align-center`` - Center-aligned image
* ``image-align-right`` - Right-aligned image
* ``image-caption-below`` - Caption appears below image
* ``image-alt-{text}`` - Alternative text
* ``image-path-{path}`` - Direct file path (alternative to image-id)

**Example:**

.. code-block:: text

   $glyph-image-id-logo-image-width-2in-image-align-center
   Company Logo
   $glyph

   $glyph-image-id-chart-image-width-4in-image-height-3in-image-caption-below
   Figure 1: Quarterly Sales Data
   $glyph

Image Registry
~~~~~~~~~~~~~~

Images must be registered before rendering:

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_docx, ImageRegistry

   # Create registry
   registry = ImageRegistry()

   # Register images
   registry.register("logo", "/path/to/logo.png")
   registry.register("chart", "/path/to/chart.jpg")

   # Render with images
   markup = """
   $glyph-image-id-logo-image-width-2in-image-align-center
   $glyph
   """

   render_markup_to_docx(markup, output_path="output.docx", image_registry=registry)

Advanced Features
-----------------

Nested Formatting
~~~~~~~~~~~~~~~~~

Utility classes can be chained to combine effects:

.. code-block:: text

   $glyph-bold-italic-underline-align-center-font-size-18-color-blue
   Multiple effects combined
   $glyph

Custom Paragraph Styles
~~~~~~~~~~~~~~~~~~~~~~~

Apply named paragraph styles:

.. code-block:: text

   $glyph-para-style-Heading1
   Heading Text
   $glyph

   $glyph-para-style-Caption
   Figure caption
   $glyph

Run-Level Styles
~~~~~~~~~~~~~~~~

Apply styles to text runs:

.. code-block:: text

   $glyph-run-style-Emphasis
   Emphasized text
   $glyph

Validation
----------

Validate markup before rendering:

.. code-block:: python

   from glyph.core.markup.parser import parse_markup
   from glyph.core.markup.validator import validate_ast

   # Parse markup
   markup = "$glyph-bold\nHello\n$glyph"
   ast = parse_markup(markup)

   # Validate
   diagnostics = validate_ast(ast)

   # Check for errors
   errors = [d for d in diagnostics if d.level == "error"]
   if errors:
       for error in errors:
           print(f"{error.level.upper()}: {error.message} (line {error.line})")

**Common Validation Errors:**

* ``UNKNOWN_UTILITY``: Utility class not registered
* ``UNBALANCED_BLOCK``: Missing ``$glyph`` closing tag
* ``SCOPE_MISMATCH``: Utility used in wrong context (e.g., image utility on paragraph)
* ``INVALID_VALUE``: Invalid parameter value (e.g., negative width)

Rendering
---------

Render to DOCX
~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_docx

   markup = """
   $glyph-bold-align-center-font-size-24
   Document Title
   $glyph

   This is body text in a regular paragraph.

   $glyph-italic
   This is an italic paragraph.
   $glyph
   """

   output_path = render_markup_to_docx(
       markup,
       output_path="output.docx",
       validate=True  # Validate before rendering
   )

Render to Bytes
~~~~~~~~~~~~~~~

Generate DOCX as bytes (no file written):

.. code-block:: python

   from glyph.core.markup.engine.integration import render_markup_to_bytes

   docx_bytes = render_markup_to_bytes(markup)

   # Upload to cloud, send via API, etc.
   upload_to_s3(docx_bytes)

Using Templates
~~~~~~~~~~~~~~~

Start from a template DOCX:

.. code-block:: python

   render_markup_to_docx(
       markup,
       template_path="template.docx",  # Use this as base
       output_path="output.docx"
   )

Best Practices
--------------

Readability
~~~~~~~~~~~

Use blank lines to separate blocks:

.. code-block:: text

   $glyph-bold
   First paragraph
   $glyph

   $glyph-italic
   Second paragraph
   $glyph

Order utility classes logically:

.. code-block:: text

   $glyph-font-size-14-bold-italic-align-center-color-blue
   Text with multiple styles
   $glyph

Maintainability
~~~~~~~~~~~~~~~

Extract common styles to variables (in Python):

.. code-block:: python

   HEADING_STYLE = "bold-font-size-18-align-center"
   BODY_STYLE = "font-size-12-line-spacing-1.5"

   markup = f"""
   $glyph-{HEADING_STYLE}
   My Heading
   $glyph

   $glyph-{BODY_STYLE}
   Body text
   $glyph
   """

Performance
~~~~~~~~~~~

For large documents, disable validation if markup is already validated:

.. code-block:: python

   render_markup_to_docx(markup, validate=False)

Examples
--------

Simple Document
~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-bold-font-size-24-align-center
   Annual Report 2025
   $glyph

   $glyph-italic-align-center
   Prepared by the Finance Team
   $glyph

   Introduction

   This report summarizes our financial performance for 2025.

   $glyph-bold
   Key Highlights:
   $glyph

   - Revenue increased by 25%
   - Expenses decreased by 10%
   - Net profit reached $5M

Document with Images
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-bold-font-size-18
   Quarterly Results
   $glyph

   Our Q4 performance exceeded expectations.

   $glyph-image-id-chart-image-width-5in-image-height-3in-image-align-center
   Figure 1: Revenue Growth
   $glyph

   As shown in the chart above, we achieved 30% growth.

Formatted Report
~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-bold-font-size-24-align-center
   Project Status Report
   $glyph

   $glyph-bold-font-size-18
   Executive Summary
   $glyph

   $glyph-line-spacing-1.5
   The project is on track to meet all milestones. Current completion is at 75%
   with an expected delivery date of March 31, 2025.
   $glyph

   $glyph-bold-font-size-18
   Progress Update
   $glyph

   $glyph-indent-left-0.5in
   Phase 1: Completed
   Phase 2: In Progress (75% complete)
   Phase 3: Not Started
   $glyph

Migration Guide
---------------

From Plain Text
~~~~~~~~~~~~~~~

**Before (plain text):**

.. code-block:: text

   My Document Title

   This is body text.

**After (Glyph markup):**

.. code-block:: text

   $glyph-bold-font-size-18
   My Document Title
   $glyph

   This is body text.

From Word
~~~~~~~~~

To convert a Word document to Glyph markup:

1. Build a schema from the DOCX
2. Use ``schema_to_plaintext()`` to generate markup
3. Edit the generated markup as needed
4. Render back to DOCX

.. code-block:: python

   from glyph.runner import build_schema, schema_to_plaintext
   from glyph.core.markup.engine.integration import render_markup_to_docx

   # Extract schema
   schema = build_schema("document.xml", "extracted/")

   # Generate markup
   markup = schema_to_plaintext(schema, "output.glyph.txt")

   # Edit output.glyph.txt as needed...

   # Render back
   render_markup_to_docx(open("output.glyph.txt").read(), output_path="final.docx")
