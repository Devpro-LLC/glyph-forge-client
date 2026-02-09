Detection & Chunking
====================

Glyph Forge includes heuristic-based form detection and document chunking features that help you pre-process content before sending it to an LLM. These tools reduce token usage, improve accuracy, and give you fine-grained control over which parts of a document get processed.

.. contents:: Quick Navigation
   :local:
   :depth: 2


Overview
--------

Two complementary capabilities:

1. **Form Detection** — classify each line of plaintext as a heading, list item, paragraph, table row, etc.
2. **Document Chunking** — split plaintext or DOCX files into heading-bounded sections

Both use the same heuristic engine under the hood and require no API calls — everything runs locally.


Form Types
----------

Glyph recognizes five categories of forms. Each is available as a Python enum for type-safe filtering.

.. code-block:: python

   from glyph_forge import HeadingForm, ListForm, ParagraphForm, TableForm, CalloutForm

Heading Forms
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Code
     - Description
   * - ``H-SHORT``
     - Short headings (≤6 words, title case or ALL CAPS)
   * - ``H-LONG``
     - Longer headings (≥7 words)
   * - ``H-SECTION-N``
     - Numbered or roman-numeral sections (1., 1.1, II., §)
   * - ``H-CONTENTS``
     - Table of contents entries (leaders + page number)
   * - ``H-SUBTITLE``
     - Subtitles / overlines (follows a title)

List Forms
~~~~~~~~~~

**Generic types:**

- ``L-BULLET`` — Generic bulleted list
- ``L-ORDERED`` — Generic ordered list
- ``L-DEFINITION`` — Definition-style lists
- ``L-CONTINUATION`` — Continuation / wrapped lines
- ``L-UNKNOWN`` — Fallback

**Granular bullet types:**

- ``L-BULLET-SOLID`` — Solid bullets (•, ●, -, \*)
- ``L-BULLET-HOLLOW`` — Hollow bullets (◦, o)
- ``L-BULLET-SQUARE`` — Square bullets (▪, ■)

**Granular ordered types:**

- ``L-ORDERED-DOTTED`` — Decimal dotted (1., 2., 3.)
- ``L-ORDERED-PARA-NUM`` — Decimal parenthesis (1), 2), 3))
- ``L-ORDERED-ROMAN-UPPER`` — Upper Roman (I., II., III.)
- ``L-ORDERED-ALPHA-UPPER`` — Upper Alpha (A., B., C.)
- ``L-ORDERED-ALPHA-LOWER-PAREN`` — Lower Alpha paren (a), b), c))
- ``L-ORDERED-ALPHA-LOWER-DOT`` — Lower Alpha dot (a., b., c.)
- ``L-ORDERED-ROMAN-LOWER`` — Lower Roman (i., ii., iii.)

Paragraph Forms
~~~~~~~~~~~~~~~

- ``P-BODY`` — Regular body text
- ``P-LEAD`` — Lead-in / first-after-heading
- ``P-SUMMARY`` — Summaries, abstracts, conclusions
- ``P-UNKNOWN`` — Fallback

Table Forms
~~~~~~~~~~~

- ``T-ROW`` — Normal data row
- ``T-HEADER`` — Header row (bold/ALL CAPS)
- ``T-CAPTION`` — Table caption / title
- ``T-FOOTNOTE`` — Notes under a table
- ``T`` — Feature-based DOCX table (from ``<w:tbl>``)

Callout Forms
~~~~~~~~~~~~~

- ``C-WARNING`` — Boxed warnings, safety notices
- ``C-QUOTE`` — Quotes, epigraphs, attributions
- ``C-CODE`` — Code or snippet blocks


Form Detection
--------------

Use ``detect_forms()`` to classify plaintext lines by heuristic form type.

Basic Example
~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   client = ForgeClient()
   ws = create_workspace()

   text = open("document.txt").read()
   result = client.detect_forms(ws, text=text)

   for c in result["classifications"]:
       print(f"{c['pattern_type']:20} {c['text'][:60]}")

Filtering by Form
~~~~~~~~~~~~~~~~~~

Only return specific form types:

.. code-block:: python

   # Get only headings and bullet lists
   result = client.detect_forms(
       ws,
       text=text,
       forms=["H-SHORT", "H-SECTION-N", "L-BULLET"],
   )

   headings = [c for c in result["classifications"] if c["pattern_type"].startswith("H-")]
   bullets = [c for c in result["classifications"] if c["pattern_type"].startswith("L-")]

Adjusting Threshold
~~~~~~~~~~~~~~~~~~~

Lower the threshold to catch more uncertain matches, or raise it for higher precision:

.. code-block:: python

   # More aggressive detection (may include false positives)
   result = client.detect_forms(ws, text=text, threshold=0.40)

   # Strict detection (only high-confidence matches)
   result = client.detect_forms(ws, text=text, threshold=0.75)

From a File
~~~~~~~~~~~

.. code-block:: python

   result = client.detect_forms_file(
       ws,
       file_path="document.txt",
       forms=["H-SHORT", "L-BULLET"],
       save_as="detection_result",
   )

Return Value
~~~~~~~~~~~~

.. code-block:: python

   {
       "classifications": [
           {
               "line_index": 0,
               "text": "INTRODUCTION",
               "pattern_type": "H-SHORT",
               "signals": ["all_caps", "short_line"],
               "score": 0.94,
               "method": "heuristic"
           },
           # ...
       ],
       "total_lines": 42,
       "matched_lines": 8,
       "forms_filter": ["H-SHORT"],
       "threshold": 0.55
   }


Document Chunking
-----------------

Chunking splits a document at heading boundaries so each section can be processed independently — for example, feeding one chunk at a time to an LLM to stay within context windows.

Chunking Plaintext
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   client = ForgeClient()
   ws = create_workspace()

   text = open("report.txt").read()
   result = client.chunk_plaintext_text(ws, text=text)

   print(f"Found {result['total_chunks']} chunks")
   for chunk in result["chunks"]:
       print(f"  {chunk['chunk_id']}: {chunk['heading_text'] or '(preamble)'}")
       print(f"    Lines {chunk['line_start']}-{chunk['line_end']}, "
             f"{len(chunk['plaintext'])} chars")

Filtering by Heading Form
~~~~~~~~~~~~~~~~~~~~~~~~~~

Only split on specific heading types:

.. code-block:: python

   # Only split on short headings and numbered sections
   result = client.chunk_plaintext_text(
       ws,
       text=text,
       heading_forms=["H-SHORT", "H-SECTION-N"],
   )

Chunking DOCX Files
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = client.chunk_docx(ws, docx_path="report.docx")

   for chunk in result["chunks"]:
       print(f"{chunk['heading_text']}: {len(chunk['plaintext'])} chars")

Chunk Return Value
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   {
       "chunks": [
           {
               "chunk_id": "chunk_0",
               "heading_text": "INTRODUCTION",
               "heading_form": "H-SHORT",
               "heading_level": 1,
               "heading_score": 0.94,
               "plaintext": "INTRODUCTION\nThis is the intro...",
               "line_start": 0,
               "line_end": 5
           },
           # ...
       ],
       "total_chunks": 4,
       "total_lines": 42,
       "headings_detected": 3
   }


CLI Commands
------------

detect-forms
~~~~~~~~~~~~

.. code-block:: bash

   # Detect all forms
   glyph-forge detect-forms document.txt

   # Filter specific forms
   glyph-forge detect-forms document.txt --forms H-SHORT,L-BULLET

   # Adjust threshold
   glyph-forge detect-forms document.txt --threshold 0.70

chunk
~~~~~

.. code-block:: bash

   # Chunk plaintext
   glyph-forge chunk report.txt

   # Chunk DOCX (auto-detected by extension)
   glyph-forge chunk report.docx

   # Filter heading forms for chunking
   glyph-forge chunk report.txt --heading-forms H-SHORT,H-SECTION-N


Use Cases
---------

Reducing LLM Token Usage
~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of sending an entire document to an LLM, chunk it first and process one section at a time:

.. code-block:: python

   result = client.chunk_plaintext_text(ws, text=full_document)

   for chunk in result["chunks"]:
       # Each chunk fits comfortably in the LLM context window
       llm_response = call_llm(chunk["plaintext"])
       process_response(chunk["chunk_id"], llm_response)

Extracting Document Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use form detection to build a table of contents or outline:

.. code-block:: python

   result = client.detect_forms(
       ws,
       text=document_text,
       forms=["H-SHORT", "H-LONG", "H-SECTION-N"],
   )

   print("Document Outline:")
   for c in result["classifications"]:
       print(f"  Line {c['line_index']}: {c['text']}")

Filtering Content by Type
~~~~~~~~~~~~~~~~~~~~~~~~~~

Extract only specific content types from a document:

.. code-block:: python

   # Get all list items from a document
   result = client.detect_forms(
       ws,
       text=document_text,
       forms=["L-BULLET", "L-ORDERED", "L-BULLET-SOLID", "L-ORDERED-DOTTED"],
   )

   list_items = [c["text"] for c in result["classifications"]]


See Also
--------

- :doc:`how_to_use` — Schema selectors and pattern matching (uses the same form types)
- :doc:`../api/client` — Full API reference for all detection and chunking methods
- :doc:`style_reference` — Style properties for schema-based formatting
