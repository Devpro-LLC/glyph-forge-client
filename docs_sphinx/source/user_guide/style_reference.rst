Style Reference
===============

This page provides a comprehensive reference for all supported style properties in Glyph Forge. Use this as a quick lookup guide when building schemas.

.. contents:: Quick Navigation
   :local:
   :depth: 2

Overview
--------

Styles in Glyph Forge are organized into four main categories:

- **font**: Text styling (size, color, bold, italic, etc.)
- **paragraph**: Paragraph formatting (alignment, spacing, borders, etc.)
- **list**: List formatting (bullets, numbering, indentation)
- **table**: Table styling (borders, alignment, headers)

.. important::
   All style properties must be nested under their category. Flat properties are not supported.

   ✅ Correct: ``{"font": {"bold": true}}``

   ❌ Wrong: ``{"bold": true}``


Font Properties
---------------

Text appearance and formatting.

Basic Properties
~~~~~~~~~~~~~~~~

name
^^^^
**Type:** string

**Description:** Font family name

**Example values:** ``"Calibri"``, ``"Arial"``, ``"Times New Roman"``, ``"Georgia"``

.. code-block:: json

   {
     "font": {
       "name": "Calibri"
     }
   }

size
^^^^
**Type:** number (points)

**Description:** Font size in points

**Common values:**
  - Body text: 10-12pt
  - Headings: 14-32pt
  - Small text: 8-9pt

.. code-block:: json

   {
     "font": {
       "size": 11
     }
   }

color
^^^^^
**Type:** string (hex RRGGBB)

**Description:** Text color as hexadecimal (without # prefix)

**Example values:** ``"000000"`` (black), ``"FF0000"`` (red), ``"1F4E78"`` (blue)

.. code-block:: json

   {
     "font": {
       "color": "1F4E78"
     }
   }

Text Style Properties
~~~~~~~~~~~~~~~~~~~~~

bold
^^^^
**Type:** boolean

**Description:** Make text bold

.. code-block:: json

   {
     "font": {
       "bold": true
     }
   }

italic
^^^^^^
**Type:** boolean

**Description:** Make text italic

.. code-block:: json

   {
     "font": {
       "italic": true
     }
   }

underline
^^^^^^^^^
**Type:** boolean OR string

**Description:** Underline text. Can be a boolean or a style name.

**Style options:** ``"single"``, ``"double"``, ``"dotted"``, ``"dashed"``, ``"wave"``

.. code-block:: json

   {
     "font": {
       "underline": true
     }
   }

.. code-block:: json

   {
     "font": {
       "underline": "double"
     }
   }

strike
^^^^^^
**Type:** boolean

**Description:** Add strikethrough to text

**Use case:** Deprecated content, deletions

.. code-block:: json

   {
     "font": {
       "strike": true,
       "color": "999999"
     }
   }

Advanced Text Properties
~~~~~~~~~~~~~~~~~~~~~~~~

highlight
^^^^^^^^^
**Type:** string

**Description:** Text highlight color (background highlight)

**Available colors:**
  - ``"yellow"``
  - ``"brightGreen"``
  - ``"turquoise"``
  - ``"pink"``
  - ``"blue"``
  - ``"red"``
  - ``"darkBlue"``
  - ``"teal"``
  - ``"green"``
  - ``"violet"``
  - ``"darkRed"``
  - ``"darkYellow"``
  - ``"gray50"``
  - ``"gray25"``

.. code-block:: json

   {
     "font": {
       "highlight": "yellow"
     }
   }

all_caps
^^^^^^^^
**Type:** boolean

**Description:** Format text in all capital letters

.. code-block:: json

   {
     "font": {
       "all_caps": true
     }
   }

small_caps
^^^^^^^^^^
**Type:** boolean

**Description:** Format text in small capitals

.. code-block:: json

   {
     "font": {
       "small_caps": true
     }
   }

hyperlink
^^^^^^^^^
**Type:** string (URL)

**Description:** Make text a clickable hyperlink

.. code-block:: json

   {
     "font": {
       "hyperlink": "https://example.com",
       "color": "0563C1",
       "underline": true
     }
   }

Complete Font Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "type": "H-SHORT",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 16,
         "bold": true,
         "italic": false,
         "color": "1F4E78",
         "underline": false
       }
     }
   }


Paragraph Properties
--------------------

Paragraph layout and spacing.

Alignment
~~~~~~~~~

alignment
^^^^^^^^^
**Type:** string

**Description:** Horizontal alignment of paragraph text

**Options:** ``"left"``, ``"center"``, ``"right"``, ``"justify"``

.. code-block:: json

   {
     "paragraph": {
       "alignment": "center"
     }
   }

Spacing
~~~~~~~

spacing_before
^^^^^^^^^^^^^^
**Type:** number (points)

**Description:** Space before the paragraph in points

**Common values:** 0-48 points

.. code-block:: json

   {
     "paragraph": {
       "spacing_before": 12
     }
   }

spacing_after
^^^^^^^^^^^^^
**Type:** number (points)

**Description:** Space after the paragraph in points

**Common values:** 0-48 points

.. code-block:: json

   {
     "paragraph": {
       "spacing_after": 12
     }
   }

line_spacing
^^^^^^^^^^^^
**Type:** number (multiplier)

**Description:** Line height multiplier

**Common values:** ``1.0`` (single), ``1.15``, ``1.5``, ``2.0`` (double)

.. code-block:: json

   {
     "paragraph": {
       "line_spacing": 1.15
     }
   }

Indentation
~~~~~~~~~~~

left_indent
^^^^^^^^^^^
**Type:** number (points)

**Description:** Left indentation in points

.. code-block:: json

   {
     "paragraph": {
       "left_indent": 360
     }
   }

right_indent
^^^^^^^^^^^^
**Type:** number (points)

**Description:** Right indentation in points

.. code-block:: json

   {
     "paragraph": {
       "right_indent": 360
     }
   }

first_line_indent
^^^^^^^^^^^^^^^^^
**Type:** number (points)

**Description:** First line indentation in points. Negative values create hanging indents.

.. code-block:: json

   {
     "paragraph": {
       "first_line_indent": 360
     }
   }

.. code-block:: json

   {
     "paragraph": {
       "first_line_indent": -360
     }
   }

Visual Effects
~~~~~~~~~~~~~~

shading
^^^^^^^
**Type:** string (hex RRGGBB) OR object

**Description:** Paragraph background color

**Format 1:** Simple hex string

.. code-block:: json

   {
     "paragraph": {
       "shading": "FFFF00"
     }
   }

**Format 2:** Object with fill property

.. code-block:: json

   {
     "paragraph": {
       "shading": {
         "fill": "FFFF00"
       }
     }
   }

borders
^^^^^^^
**Type:** object

**Description:** Paragraph borders on any side (top, bottom, left, right)

**Border properties:**
  - ``color``: Hex color (e.g., ``"FF0000"``)
  - ``size``: Border width in eighths of a point (default: 6 = 0.75pt)
  - ``style``: Border style (``"single"``, ``"double"``, ``"dotted"``, etc.)
  - ``space``: Space between border and text in points (default: 1)

.. code-block:: json

   {
     "paragraph": {
       "borders": {
         "bottom": {
           "color": "1F4E78",
           "size": 12,
           "style": "single",
           "space": 1
         }
       }
     }
   }

.. code-block:: json

   {
     "paragraph": {
       "borders": {
         "top": {"color": "000000", "size": 6},
         "bottom": {"color": "000000", "size": 6},
         "left": {"color": "000000", "size": 6},
         "right": {"color": "000000", "size": 6}
       }
     }
   }

Complete Paragraph Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "paragraph": {
         "alignment": "justify",
         "spacing_before": 6,
         "spacing_after": 6,
         "line_spacing": 1.15,
         "left_indent": 0,
         "right_indent": 0,
         "first_line_indent": 0
       }
     }
   }


List Properties
---------------

List formatting and numbering.

Format Properties
~~~~~~~~~~~~~~~~~

format
^^^^^^
**Type:** string

**Description:** List number/bullet format

**Options:**
  - ``"bullet"`` - Bullet points
  - ``"decimal"`` - 1, 2, 3
  - ``"upperRoman"`` - I, II, III
  - ``"lowerRoman"`` - i, ii, iii
  - ``"upperLetter"`` - A, B, C
  - ``"lowerLetter"`` - a, b, c

.. code-block:: json

   {
     "list": {
       "format": "decimal"
     }
   }

numId
^^^^^
**Type:** string

**Description:** DOCX numbering definition ID

**Standard IDs:**
  - ``"1"`` - L-BULLET-SOLID (•, ●, -, *)
  - ``"4"`` - L-BULLET-HOLLOW (◦, o)
  - ``"5"`` - L-BULLET-SQUARE (▪, ■)
  - ``"6"`` - L-ORDERED-DOTTED (1., 2., 3.)
  - ``"7"`` - L-ORDERED-PARA-NUM (1), 2), 3))
  - ``"8"`` - L-ORDERED-ROMAN-UPPER (I., II., III.)
  - ``"9"`` - L-ORDERED-ALPHA-UPPER (A., B., C.)
  - ``"10"`` - L-ORDERED-ALPHA-LOWER-PAREN (a), b), c))
  - ``"11"`` - L-ORDERED-ALPHA-LOWER-DOT (a., b., c.)
  - ``"12"`` - L-ORDERED-ROMAN-LOWER (i., ii., iii.)

.. code-block:: json

   {
     "list": {
       "numId": "6"
     }
   }

ilvl
^^^^
**Type:** string

**Description:** Indentation level (0-based)

**Common values:** ``"0"`` (first level), ``"1"`` (nested), ``"2"`` (double-nested)

.. code-block:: json

   {
     "list": {
       "ilvl": "0"
     }
   }

lvlText
^^^^^^^
**Type:** string

**Description:** Level text template or bullet character

**Examples:**
  - ``"•"`` - Solid bullet
  - ``"◦"`` - Hollow bullet
  - ``"%1."`` - Number with period (1., 2., 3.)
  - ``"%1)"`` - Number with parenthesis (1), 2), 3))

.. code-block:: json

   {
     "list": {
       "lvlText": "•"
     }
   }

numFmt
^^^^^^
**Type:** string

**Description:** Number format (typically same as ``format``)

.. code-block:: json

   {
     "list": {
       "numFmt": "decimal"
     }
   }

Deprecated Properties
~~~~~~~~~~~~~~~~~~~~~

.. warning::
   These properties are deprecated but still supported for backward compatibility.

list_type
^^^^^^^^^
**Type:** string

**Description:** (Deprecated) Use ``format`` instead

**Options:** ``"bullet"``, ``"number"``

list_level
^^^^^^^^^^
**Type:** number

**Description:** (Deprecated) Use ``ilvl`` instead

**Range:** 1-9

Complete List Example
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "type": "L-ORDERED-DOTTED",
     "style": {
       "list": {
         "format": "decimal",
         "numId": "6",
         "ilvl": "0",
         "lvlText": "%1.",
         "numFmt": "decimal"
       },
       "font": {
         "name": "Calibri",
         "size": 11
       },
       "paragraph": {
         "spacing_after": 6
       }
     }
   }


Table Properties
----------------

Table styling and layout.

Table Structure
~~~~~~~~~~~~~~~

table_style
^^^^^^^^^^^
**Type:** string

**Description:** DOCX table style name

**Common values:**
  - ``"Table Grid"``
  - ``"Light Shading"``
  - ``"Light Shading Accent 1"``
  - ``"Medium Shading 1"``
  - ``"Table Grid Light"``

.. code-block:: json

   {
     "table": {
       "table_style": "Light Shading Accent 1"
     }
   }

alignment
^^^^^^^^^
**Type:** string

**Description:** Table alignment on the page

**Options:** ``"left"``, ``"center"``, ``"right"``

.. code-block:: json

   {
     "table": {
       "alignment": "center"
     }
   }

borders
^^^^^^^
**Type:** string

**Description:** Table border style

**Options:**
  - ``"all"`` - All borders (outer + inner)
  - ``"outer"`` - Only outer borders
  - ``"none"`` - No borders

.. code-block:: json

   {
     "table": {
       "borders": "all"
     }
   }

Layout Properties
~~~~~~~~~~~~~~~~~

autofit
^^^^^^^
**Type:** boolean

**Description:** Auto-fit table to content width

.. code-block:: json

   {
     "table": {
       "autofit": true
     }
   }

col_widths
^^^^^^^^^^
**Type:** array of numbers (inches)

**Description:** Column widths in inches

.. code-block:: json

   {
     "table": {
       "col_widths": [1.5, 2.0, 1.0]
     }
   }

Header Properties
~~~~~~~~~~~~~~~~~

header_rows
^^^^^^^^^^^
**Type:** number

**Description:** Number of header rows (typically 1)

.. code-block:: json

   {
     "table": {
       "header_rows": 1
     }
   }

header_shading
^^^^^^^^^^^^^^
**Type:** string (hex RRGGBB)

**Description:** Background color for header rows

.. code-block:: json

   {
     "table": {
       "header_shading": "1F4E78"
     }
   }

Cell Properties
~~~~~~~~~~~~~~~

cell_alignment
^^^^^^^^^^^^^^
**Type:** string

**Description:** Default cell text alignment

**Options:** ``"left"``, ``"center"``, ``"right"``, ``"justify"``

.. code-block:: json

   {
     "table": {
       "cell_alignment": "center"
     }
   }

Complete Table Example
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "type": "T-ROW",
     "style": {
       "table": {
         "table_style": "Light Shading Accent 1",
         "alignment": "center",
         "borders": "all",
         "autofit": true,
         "col_widths": [2.0, 3.0, 2.0],
         "header_rows": 1,
         "header_shading": "1F4E78",
         "cell_alignment": "left"
       },
       "font": {
         "name": "Calibri",
         "size": 10
       },
       "paragraph": {
         "spacing_after": 6
       }
     }
   }


Common Patterns
---------------

This section provides ready-to-use patterns for common styling scenarios.

Styled Headers
~~~~~~~~~~~~~~

**Centered Title Header**

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
         "spacing_after": 24
       }
     }
   }

**Section Header with Background**

.. code-block:: json

   {
     "type": "H-SHORT",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 14,
         "bold": true,
         "color": "FFFFFF"
       },
       "paragraph": {
         "alignment": "left",
         "spacing_after": 12,
         "shading": "1F4E78"
       }
     }
   }

**Section Header with Bottom Border**

.. code-block:: json

   {
     "type": "H-SHORT",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 16,
         "bold": true,
         "color": "1F4E78"
       },
       "paragraph": {
         "alignment": "left",
         "spacing_after": 12,
         "borders": {
           "bottom": {
             "color": "1F4E78",
             "size": 12,
             "style": "single"
           }
         }
       }
     }
   }

Body Text Variations
~~~~~~~~~~~~~~~~~~~~

**Standard Body Text**

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 11
       },
       "paragraph": {
         "alignment": "left",
         "line_spacing": 1.15,
         "spacing_after": 6
       }
     }
   }

**Justified Paragraph**

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "font": {
         "name": "Times New Roman",
         "size": 12
       },
       "paragraph": {
         "alignment": "justify",
         "line_spacing": 1.5,
         "spacing_after": 12
       }
     }
   }

**Indented Quote**

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "font": {
         "name": "Georgia",
         "size": 11,
         "italic": true
       },
       "paragraph": {
         "alignment": "left",
         "left_indent": 720,
         "right_indent": 720,
         "spacing_before": 12,
         "spacing_after": 12,
         "shading": "F5F5F5"
       }
     }
   }

**Highlighted Important Text**

.. code-block:: json

   {
     "type": "P-BODY",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 11,
         "highlight": "yellow"
       },
       "paragraph": {
         "spacing_after": 6
       }
     }
   }

Lists
~~~~~

**Simple Bullet List**

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
         "spacing_after": 6
       }
     }
   }

**Numbered List**

.. code-block:: json

   {
     "type": "L-ORDERED-DOTTED",
     "style": {
       "list": {
         "format": "decimal",
         "numId": "6",
         "ilvl": "0"
       },
       "font": {
         "name": "Calibri",
         "size": 11,
         "bold": true
       },
       "paragraph": {
         "spacing_after": 6
       }
     }
   }

Tables
~~~~~~

**Simple Data Table**

.. code-block:: json

   {
     "type": "T-ROW",
     "style": {
       "table": {
         "table_style": "Table Grid",
         "alignment": "left",
         "borders": "all",
         "autofit": true,
         "header_rows": 1
       },
       "font": {
         "name": "Calibri",
         "size": 10
       }
     }
   }

**Styled Table with Headers**

.. code-block:: json

   {
     "type": "T-ROW",
     "style": {
       "table": {
         "table_style": "Light Shading Accent 1",
         "alignment": "center",
         "borders": "all",
         "autofit": true,
         "header_rows": 1,
         "header_shading": "1F4E78",
         "cell_alignment": "center"
       },
       "font": {
         "name": "Calibri",
         "size": 10
       }
     }
   }


Quick Reference
---------------

Color Values
~~~~~~~~~~~~

Common hex colors (no # prefix):

.. code-block:: text

   000000 - Black
   FFFFFF - White
   FF0000 - Red
   00FF00 - Green
   0000FF - Blue
   FFFF00 - Yellow
   FF00FF - Magenta
   00FFFF - Cyan

   1F4E78 - Dark Blue (common for headings)
   0563C1 - Hyperlink Blue
   C0504D - Dark Red
   9BBB59 - Olive Green
   8064A2 - Purple
   4BACC6 - Teal
   F79646 - Orange

   999999 - Light Gray
   666666 - Medium Gray
   333333 - Dark Gray

Highlight Colors
~~~~~~~~~~~~~~~~

Available highlight color names:

.. code-block:: text

   yellow
   brightGreen
   turquoise
   pink
   blue
   red
   darkBlue
   teal
   green
   violet
   darkRed
   darkYellow
   gray50
   gray25

Spacing Guidelines
~~~~~~~~~~~~~~~~~~

Common spacing values in points:

.. code-block:: text

   6pt   - Tight spacing (between list items)
   12pt  - Normal spacing (between paragraphs)
   24pt  - Section spacing (after headers)
   48pt  - Large spacing (between major sections)

Font Sizes
~~~~~~~~~~

Standard font sizes:

.. code-block:: text

   8-9pt   - Small text (captions, footnotes)
   10-12pt - Body text
   14-16pt - Subheadings
   18-24pt - Major headings
   28-32pt - Titles

Indentation
~~~~~~~~~~~

Common indentation values (1 inch = 72 points = 1440 twips):

.. code-block:: text

   360pt  - 0.5 inch indent
   720pt  - 1 inch indent
   1080pt - 1.5 inch indent
   1440pt - 2 inch indent


Best Practices
--------------

Nesting Requirements
~~~~~~~~~~~~~~~~~~~~

**Always nest style properties under their category:**

.. code-block:: json

   {
     "style": {
       "font": {
         "size": 11,
         "bold": true
       },
       "paragraph": {
         "alignment": "left"
       }
     }
   }

Color Format
~~~~~~~~~~~~

**Always use hex colors without # prefix:**

✅ Correct: ``"color": "FF0000"``

❌ Wrong: ``"color": "#FF0000"``

Combining Styles
~~~~~~~~~~~~~~~~

**You can combine font, paragraph, list, and table properties:**

.. code-block:: json

   {
     "type": "L-BULLET-SOLID",
     "style": {
       "font": {
         "name": "Calibri",
         "size": 11,
         "color": "1F4E78"
       },
       "paragraph": {
         "alignment": "left",
         "spacing_after": 6,
         "left_indent": 360
       },
       "list": {
         "format": "bullet",
         "ilvl": "0"
       }
     }
   }

Testing Styles
~~~~~~~~~~~~~~

When building a schema:

1. Start with basic properties (font name, size)
2. Add alignment and spacing
3. Test with sample content
4. Add advanced properties (borders, shading) as needed
5. Verify output in Word


Inline Markup Equivalents
-------------------------

The font properties documented above can also be applied directly in plaintext using Glyph's inline markup syntax. This is useful when you want to style specific words without schema selectors.

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Schema Property
     - Block Markup
     - Inline Markup
   * - ``"bold": true``
     - ``$glyph-bold``
     - ``[bold]text[/]``
   * - ``"italic": true``
     - ``$glyph-italic``
     - ``[italic]text[/]``
   * - ``"size": 14``
     - ``$glyph-font-size-14``
     - ``[font-size-14]text[/]``
   * - ``"color": "FF0000"``
     - ``$glyph-color-FF0000``
     - ``[color-FF0000]text[/]``
   * - ``"highlight": "yellow"``
     - ``$glyph-highlight-yellow``
     - ``[highlight-yellow]text[/]``
   * - ``"underline": true``
     - ``$glyph-underline``
     - ``[underline]text[/]``
   * - ``"name": "Arial"``
     - ``$glyph-font-name-arial``
     - ``[font-name-arial]text[/]``

Multiple inline utilities can be combined with commas: ``[bold,color-FF0000]text[/]``

For the complete inline markup reference, see :doc:`markup_reference`.


See Also
--------

- :doc:`how_to_use` - Complete guide to selectors and patterns
- :doc:`markup_reference` - Inline markup syntax reference
- :doc:`quickstart` - Get started quickly with examples
- :doc:`../examples/basic_usage` - More usage examples
