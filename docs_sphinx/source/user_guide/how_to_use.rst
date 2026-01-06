How to Use
==========

Quick Start
-----------

Introduction
~~~~~~~~~~~~

Glyph is a LLM to DOCX Framework inspired by HTML, CSS, and Tailwind design patterns. While HTML uses elements and CSS uses "selectors", Glyph uses predefined heuristics that can be activated in the schema as a selector object. Glyph also offers Tailwind-inspired inline markup for layout-based compiling such as columns.

Heuristics and Styles Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Just like HTML elements that map to CSS selectors, we have heuristic codes, exact matching, and custom regex.

Headings
--------

Types
~~~~~

.. code-block:: text

   "H-SHORT"         # Short headings (≤6 words, title/ALLCAPS)
   "H-LONG"          # Longer headings (≥7 words)
   "H-SECTION-N"     # Numbered/roman section (1., 1.1, II., §)
   "H-CONTENTS"      # Table of contents entry (leaders + page #)
   "H-SUBTITLE"      # Subtitle / overline (follows a title)

Example
~~~~~~~

.. code-block:: json

   {
     "type": "H-SHORT",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 24,
         "bold": true,
         "color": "1F4E78"
       },
       "paragraph": {
         "alignment": "center",
         "spacing_after": 240
       }
     }
   }

Paragraphs
----------

Types
~~~~~

.. code-block:: text

   "P-BODY"      # Regular body text
   "P-UNKNOWN"   # Fallback

Example
~~~~~~~

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "font": {
         "name": "Arial",
         "size": 12
       },
       "paragraph": {
         "alignment": "center",
         "spacing_after": 60
       }
     }
   }

Lists
-----

Types
~~~~~

**Generic types (backward compatibility):**

.. code-block:: text

   "L-BULLET"        # Generic bulleted list
   "L-ORDERED"       # Generic ordered list
   "L-DEFINITION"    # Definition-style lists
   "L-CONTINUATION"  # Continuation / wrapped lines
   "L-UNKNOWN"       # Fallback

**Granular bullet types:**

.. code-block:: text

   "L-BULLET-SOLID"   # Solid bullets (•, ●, -, *) - numId: 1
   "L-BULLET-HOLLOW"  # Hollow bullets (◦, o) - numId: 4
   "L-BULLET-SQUARE"  # Square bullets (▪, ■) - numId: 5

**Granular ordered types:**

.. code-block:: text

   "L-ORDERED-DOTTED"             # Decimal dotted (1., 2., 3.) - numId: 6
   "L-ORDERED-PARA-NUM"           # Decimal parenthesis (1), 2), 3)) - numId: 7
   "L-ORDERED-ROMAN-UPPER"        # Upper Roman (I., II., III.) - numId: 8
   "L-ORDERED-ALPHA-UPPER"        # Upper Alpha (A., B., C.) - numId: 9
   "L-ORDERED-ALPHA-LOWER-PAREN"  # Lower Alpha paren (a), b), c)) - numId: 10
   "L-ORDERED-ALPHA-LOWER-DOT"    # Lower Alpha dot (a., b., c.) - numId: 11
   "L-ORDERED-ROMAN-LOWER"        # Lower Roman (i., ii., iii.) - numId: 12

Example
~~~~~~~

.. code-block:: json

   {
     "type": "L-BULLET-SOLID",
     "style": {
       "list": {
         "format": "bullet",
         "numId": "1",
         "ilvl": "0"
       },
       "font": {
         "name": "Calibri",
         "size": 11
       },
       "paragraph": {
         "spacing_after": 60
       }
     }
   }

Tables
------

``T-ROW`` selects a line of plaintext containing text separated by pipes.

Example
~~~~~~~

**Plaintext input:**

.. code-block:: text

   col1 | col2 | col3
   data1 | data2 | data3

**Selector:**

.. code-block:: json

   {
     "type": "T-ROW",
     "style": {
       "style_id": "TableRow",
       "font": {
         "name": "Calibri",
         "size": 10,
         "color": "000000"
       },
       "paragraph": {
         "alignment": "left",
         "spacing_after": 10,
         "borders": {
           "bottom": {
             "color": "D9D9D9",
             "size": 6,
             "style": "single"
           }
         }
       }
     }
   }

Design Philosophy and Edge Cases
---------------------------------

If used correctly, Glyph Forge can save hours, days, or even months of LLM to DOCX work with a single schema.

Philosophy
~~~~~~~~~~

Think about the type of document you are working with and list out the elements the document will have. Does it have headings, paragraphs, tables, or lists? Create selectors for the types the document requires, then check for edge cases.

Edge Cases
~~~~~~~~~~

Using the HTML/CSS analogy, sometimes you need to create custom elements when making a website. The same applies to LLM to DOCX automation. Your document may require custom regex selectors and/or exact matches in addition to the predefined heuristics.

Exact Matching and Custom Regex
--------------------------------

Routing Priority
~~~~~~~~~~~~~~~~

The pattern matching engine follows this priority order:

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │  1. EXACT MATCHER                       │  ← Highest priority
   │     Match exact strings from domain     │
   ├─────────────────────────────────────────┤
   │  2. HEURISTIC CLASSIFIERS               │
   │     • Heading (H-) Detector             │
   │     • List (L-) Detector                │
   │     • Paragraph (P-) Detector           │
   │     • Table (T-) Detector               │
   ├─────────────────────────────────────────┤
   │  3. REGEX MATCHER                       │  ← Fallback
   │     Pattern-based normalization         │
   └─────────────────────────────────────────┘

Exact Match
~~~~~~~~~~~

**When to use:** You want to select an exact string such as a company name, warning label, or sequence of chapter/section titles.

**Syntax:** ``EXACT:<string>`` — Specify the string to select

**Example:**

.. code-block:: json

   {
     "type": "EXACT:Warnings and Precautions:",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 18,
         "bold": true,
         "color": "C0504D"
       },
       "paragraph": {
         "alignment": "left",
         "spacing_before": 120,
         "spacing_after": 60
       }
     }
   }

Custom Regex
~~~~~~~~~~~~

**When to use:** You want to select one or more plaintext lines that fit a regex pattern. This is useful for date strings, common patterns such as (Location, City, Zip), etc.

**Syntax:** ``REGEX:<pattern>`` — Specify the regex you want to select

**Example 1: Select texts with "Urgent"**

.. code-block:: json

   {
     "id": "P-IMPORTANT",
     "type": "REGEX:^URGENT.*$",
     "style": {
       "font": {
         "bold": true,
         "color": "FF0000"
       }
     }
   }

**Example 2: Select date patterns**

.. code-block:: json

   {
     "id": "P-DATE-FLEXIBLE",
     "type": "REGEX:^\\d+/\\d+/\\d+$",
     "features": {
       "text": "12/25/2024"
     },
     "style": {
       "font": {
         "color": "FF0000"
       }
     }
   }

Mixed Pattern Types
~~~~~~~~~~~~~~~~~~~

You can mix EXACT and REGEX in the same array:

.. code-block:: json

   {
     "type": [
       "EXACT:Education",
       "EXACT:Experience",
       "REGEX:^[A-Z][a-z]+\\sEducation$",
       "REGEX:^[A-Z][a-z]+\\sTechnical Skills$"
     ],
     "style": {
       "font": {
         "bold": true,
         "size": 14
       }
     }
   }

Additional Notes
~~~~~~~~~~~~~~~~

**Custom IDs:**

You can add an ID to any selector. This has no effect on compiling the DOCX; it's just to give a custom ID to your selector for readability and organization. These are very useful as labels for regex and exact matches.

.. code-block:: json

   {
     "id": "my-custom-heading",
     "type": "H-SHORT",
     "style": {}
   }

**Features Field:**

The ``features`` field is also optional and does not compile. This is useful to describe the features of the text your regex selector is targeting.

.. code-block:: json

   {
     "type": "REGEX:^\\d{3}-\\d{3}-\\d{4}$",
     "features": {
       "text": "Phone number pattern: 555-123-4567"
     },
     "style": {}
   }

Next Steps
----------

Now that you understand the basics of Glyph selectors and patterns, you can:

1. Review the :doc:`../api/client` for detailed API documentation
2. Explore more examples in the :doc:`../examples/basic_usage` section
3. Learn about advanced features in the :doc:`quickstart` guide
