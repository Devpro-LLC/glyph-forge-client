Detection, Chunking & Indexing
===============================

Glyph Forge includes heuristic-based form detection, document chunking, and document indexing features that help you pre-process content before sending it to an LLM. These tools reduce token usage, improve accuracy, and give you fine-grained control over which parts of a document get processed.

.. contents:: Quick Navigation
   :local:
   :depth: 2


Overview
--------

Three complementary capabilities:

1. **Form Detection** — classify each line of plaintext as a heading, list item, paragraph, table row, etc.
2. **Document Chunking** — split plaintext or DOCX files into heading-bounded sections
3. **Document Indexing** — build a structured index with heading-bounded sections *and* form-annotated segments within each section

All three use the same heuristic engine under the hood and require no API calls — everything runs locally.

**When to use which:**

- Use **Form Detection** when you need to know *what* each line is (classification only, no structure).
- Use **Document Chunking** when you need to split a document into independent sections for per-section processing.
- Use **Document Indexing** when you need both the section structure *and* the ability to locate and extract specific content types (bullet lists, table rows, etc.) within each section.


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


Document Indexing
-----------------

Purpose
~~~~~~~

Form detection tells you *what* each line is, and chunking splits a document at heading boundaries — but neither gives you a structured view that combines both. If you want to answer "give me every bullet list in Section 3" or "extract all table rows under the Requirements heading," you need to do manual bookkeeping to correlate line classifications with section boundaries.

**Document indexing closes that gap.** It builds a structured index where every heading-bounded **section** carries its own metadata (heading text, form, level, score, line span) *and* an array of **segments** — contiguous runs of a specific form type annotated within that section. Segments let you pinpoint exactly where bullet lists, table rows, ordered lists, or any other form type appear and pull their content directly.

This is the plaintext equivalent of the XML agent's ``ChunkIndexer``: a single call gives you a navigable document map that you can use to build heuristic pre-processing pipelines — extracting exactly what you need before calling an LLM, reducing tokens, cost, and noise.

**Key properties:**

- Sections are bounded by headings (same algorithm as chunking)
- Segments are contiguous runs of a single form type within a section
- Blank lines break segments (two bullet groups separated by a blank → two segments)
- Content before the first heading goes into a ``preamble`` object (not a section)
- Setting ``annotate_forms=None`` skips classification entirely (faster — segments are ``[]``)
- All processing is local, no API key required, runs in milliseconds

When to Use Indexing
~~~~~~~~~~~~~~~~~~~~

Use ``index_document()`` instead of ``chunk_plaintext_text()`` when:

- You need to **locate specific content types** within sections (e.g. "all bullets under Requirements")
- You want **segment-level spans** so you can slice content by form type, not just by section
- You're building a **pre-processing pipeline** that extracts structured data before sending it to an LLM
- You need **heading metadata** (level, numbering, form) alongside section content in one call

Use ``chunk_plaintext_text()`` when you only need to split a document into sections and don't care about what's inside each one.

Basic Indexing
~~~~~~~~~~~~~~

.. code-block:: python

   from glyph_forge import ForgeClient, create_workspace

   client = ForgeClient()
   ws = create_workspace()

   text = open("report.txt").read()
   result = client.index_document(ws, text=text)

   print(f"Found {result['total_sections']} sections")
   for sec in result["sections"]:
       print(f"  {sec['section_id']}: {sec['heading']['text']}")
       print(f"    Lines {sec['span']['start']}-{sec['span']['end']}")

Indexing with Annotations
~~~~~~~~~~~~~~~~~~~~~~~~~

Add segment annotations to identify contiguous runs of specific form types within each section:

.. code-block:: python

   result = client.index_document(
       ws,
       text=text,
       annotate_forms=["L-BULLET", "T-ROW"],
   )

   for sec in result["sections"]:
       print(f"\n{sec['heading']['text']}:")
       for seg in sec["segments"]:
           print(f"  {seg['form']}: {seg['count']} lines "
                 f"(lines {seg['span']['start']}-{seg['span']['end']})")

Selective Section Forms
~~~~~~~~~~~~~~~~~~~~~~~~

Only split on specific heading types:

.. code-block:: python

   # Only treat H-SHORT and H-SECTION-N as section boundaries
   result = client.index_document(
       ws,
       text=text,
       section_forms=["H-SHORT", "H-SECTION-N"],
       annotate_forms=["L-BULLET"],
   )

Indexing DOCX Files
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   result = client.index_docx(
       ws,
       docx_path="report.docx",
       annotate_forms=["L-BULLET", "T-ROW"],
   )

   for sec in result["sections"]:
       print(f"{sec['heading']['text']}: {len(sec['segments'])} segments")

Selective Extraction
~~~~~~~~~~~~~~~~~~~~~

Use the index to extract only what you need before calling an LLM:

.. code-block:: python

   result = client.index_document(
       ws,
       text=text,
       annotate_forms=["L-BULLET", "T-ROW"],
   )

   # Extract only bullet lists from each section
   for sec in result["sections"]:
       bullets = [s for s in sec["segments"] if s["form"] == "L-BULLET"]
       if bullets:
           print(f"Bullets in '{sec['heading']['text']}':")
           for b in bullets:
               print(b["content"])

Index Return Value
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   {
       "sections": [
           {
               "section_id": "sec_0",
               "heading": {
                   "text": "Introduction",
                   "form": "H-SHORT",
                   "line": 0,
                   "score": 0.94,
                   "level": 1,
                   "numbering": None
               },
               "span": {"start": 0, "end": 15},
               "content": "Introduction\nThis is the intro...",
               "segments": [
                   {
                       "form": "L-BULLET",
                       "span": {"start": 5, "end": 8},
                       "content": "- First\n- Second\n- Third",
                       "count": 3
                   }
               ]
           }
       ],
       "preamble": {
           "span": {"start": 0, "end": 0},
           "content": "",
           "segments": []
       },
       "total_sections": 1,
       "total_lines": 15,
       "headings_detected": 1,
       "section_forms": ["H-SHORT", "H-LONG", "H-SECTION-N", "H-CONTENTS", "H-SUBTITLE"],
       "annotate_forms": ["L-BULLET"]
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

index
~~~~~

.. code-block:: bash

   # Index plaintext with all heading forms
   glyph-forge index document.txt

   # Index DOCX (auto-detected by extension)
   glyph-forge index report.docx

   # Annotate specific form types as segments
   glyph-forge index document.txt --annotate-forms L-BULLET,T-ROW

   # Filter section heading forms
   glyph-forge index document.txt --section-forms H-SHORT,H-SECTION-N

   # Verbose output with segment details
   glyph-forge index document.txt --annotate-forms L-BULLET -v


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

Targeted LLM Extraction with Indexing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use document indexing to extract only specific content types from each section, then send just those pieces to an LLM:

.. code-block:: python

   result = client.index_document(
       ws,
       text=full_document,
       annotate_forms=["L-BULLET", "T-ROW"],
   )

   for sec in result["sections"]:
       # Only process sections that contain bullet lists
       bullets = [s for s in sec["segments"] if s["form"] == "L-BULLET"]
       if bullets:
           # Send only the bullet content — not the entire section
           for seg in bullets:
               summary = call_llm(f"Summarize these items:\n{seg['content']}")
               print(f"{sec['heading']['text']}: {summary}")

       # Extract table data separately
       tables = [s for s in sec["segments"] if s["form"] == "T-ROW"]
       if tables:
           for seg in tables:
               parsed = call_llm(f"Parse this table into JSON:\n{seg['content']}")
               save_structured_data(sec["section_id"], parsed)

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
- :doc:`../api/client` — Full API reference for all detection, chunking, and indexing methods
- :doc:`cli` — CLI reference for ``detect-forms``, ``chunk``, and ``index`` commands
- :doc:`style_reference` — Style properties for schema-based formatting
