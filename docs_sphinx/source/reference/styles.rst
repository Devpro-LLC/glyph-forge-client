Style Reference
===============

The Glyph SDK uses a comprehensive style system for controlling document appearance. Styles are defined in schema pattern descriptors and applied during document generation.

Style Object Structure
----------------------

A style object contains properties for fonts, paragraphs, and lists:

.. code-block:: python

   {
       "style_id": "Heading1",           # Reference to Word style
       "font": {                         # Font/run-level properties
           "name": "Arial",
           "size": 14,
           "bold": True,
           "italic": False,
           "underline": True,
           "color": "FF0000"
       },
       "paragraph": {                    # Paragraph-level properties
           "alignment": "left",
           "spacing_before": 240,
           "spacing_after": 120,
           "line_spacing": 1.15,
           "shading": "FFFF00"
       },
       "list": {                         # List properties (if applicable)
           "numId": "1",
           "ilvl": "0",
           "format": "bullet",
           "lvlText": "•"
       }
   }

Font Properties
---------------

Font properties control text appearance at the run level.

Basic Font Properties
~~~~~~~~~~~~~~~~~~~~~

name
^^^^
**Type:** ``str``

**Description:** Font family name

**Example:**

.. code-block:: python

   "font": {
       "name": "Arial"
   }

**Supported values:**

* ``"Arial"``
* ``"Times New Roman"``
* ``"Calibri"``
* ``"Courier New"``
* Any installed system font

size
^^^^
**Type:** ``int`` or ``float``

**Description:** Font size in points

**Example:**

.. code-block:: python

   "font": {
       "size": 12
   }

**Common values:**

* ``10`` - Small text
* ``11`` - Default body text
* ``12`` - Standard body text
* ``14`` - Subheading
* ``18`` - Heading
* ``24`` - Title

Text Formatting
~~~~~~~~~~~~~~~

bold
^^^^
**Type:** ``bool``

**Description:** Apply bold formatting

**Example:**

.. code-block:: python

   "font": {
       "bold": True
   }

italic
^^^^^^
**Type:** ``bool``

**Description:** Apply italic formatting

**Example:**

.. code-block:: python

   "font": {
       "italic": True
   }

underline
^^^^^^^^^
**Type:** ``bool`` or ``str``

**Description:** Apply underline formatting

**Example:**

.. code-block:: python

   "font": {
       "underline": True  # Single underline
   }

   "font": {
       "underline": "double"  # Double underline
   }

**Supported values:**

* ``True`` - Single underline
* ``False`` - No underline
* ``"single"`` - Single underline
* ``"double"`` - Double underline
* ``"thick"`` - Thick underline
* ``"dotted"`` - Dotted underline
* ``"dash"`` - Dashed underline

strike
^^^^^^
**Type:** ``bool``

**Description:** Apply strikethrough formatting

**Example:**

.. code-block:: python

   "font": {
       "strike": True
   }

all_caps
^^^^^^^^
**Type:** ``bool``

**Description:** Convert text to all uppercase

**Example:**

.. code-block:: python

   "font": {
       "all_caps": True
   }

small_caps
^^^^^^^^^^
**Type:** ``bool``

**Description:** Apply small caps formatting

**Example:**

.. code-block:: python

   "font": {
       "small_caps": True
   }

Color Properties
~~~~~~~~~~~~~~~~

color
^^^^^
**Type:** ``str``

**Description:** Text color in hexadecimal RGB format

**Example:**

.. code-block:: python

   "font": {
       "color": "FF0000"  # Red
   }

   "font": {
       "color": "#0000FF"  # Blue (# prefix optional)
   }

**Common colors:**

* ``"000000"`` - Black
* ``"FFFFFF"`` - White
* ``"FF0000"`` - Red
* ``"00FF00"`` - Green
* ``"0000FF"`` - Blue
* ``"FFFF00"`` - Yellow
* ``"FF00FF"`` - Magenta
* ``"00FFFF"`` - Cyan

highlight
^^^^^^^^^
**Type:** ``str``

**Description:** Background highlight color

**Example:**

.. code-block:: python

   "font": {
       "highlight": "yellow"
   }

**Supported values:**

* ``"yellow"``
* ``"brightGreen"``
* ``"turquoise"``
* ``"pink"``
* ``"blue"``
* ``"red"``
* ``"darkBlue"``
* ``"teal"``
* ``"green"``
* ``"violet"``
* ``"darkRed"``
* ``"darkYellow"``
* ``"gray50"``
* ``"gray25"``

Hyperlinks
~~~~~~~~~~

hyperlink
^^^^^^^^^
**Type:** ``str``

**Description:** URL for hyperlinked text

**Example:**

.. code-block:: python

   "font": {
       "hyperlink": "https://example.com"
   }

Paragraph Properties
--------------------

Paragraph properties control block-level formatting.

Alignment
~~~~~~~~~

alignment
^^^^^^^^^
**Type:** ``str``

**Description:** Horizontal text alignment

**Example:**

.. code-block:: python

   "paragraph": {
       "alignment": "center"
   }

**Supported values:**

* ``"left"`` - Left-aligned (default)
* ``"center"`` - Center-aligned
* ``"right"`` - Right-aligned
* ``"justify"`` - Justified (align both left and right)

Spacing
~~~~~~~

spacing_before
^^^^^^^^^^^^^^
**Type:** ``int``

**Description:** Space before paragraph in twips (1/20 of a point)

**Example:**

.. code-block:: python

   "paragraph": {
       "spacing_before": 240  # 12 points (240/20)
   }

**Common values:**

* ``0`` - No spacing
* ``120`` - 6 points
* ``240`` - 12 points (standard)
* ``480`` - 24 points

spacing_after
^^^^^^^^^^^^^
**Type:** ``int``

**Description:** Space after paragraph in twips

**Example:**

.. code-block:: python

   "paragraph": {
       "spacing_after": 120  # 6 points
   }

line_spacing
^^^^^^^^^^^^
**Type:** ``float``

**Description:** Line spacing multiplier

**Example:**

.. code-block:: python

   "paragraph": {
       "line_spacing": 1.5  # 1.5x line spacing
   }

**Common values:**

* ``1.0`` - Single spacing
* ``1.15`` - Default Word spacing
* ``1.5`` - 1.5 line spacing
* ``2.0`` - Double spacing

Indentation
~~~~~~~~~~~

left_indent
^^^^^^^^^^^
**Type:** ``int``

**Description:** Left indentation in twips

**Example:**

.. code-block:: python

   "paragraph": {
       "left_indent": 720  # 0.5 inch (720 twips)
   }

**Common values:**

* ``0`` - No indentation
* ``360`` - 0.25 inch
* ``720`` - 0.5 inch
* ``1440`` - 1 inch

right_indent
^^^^^^^^^^^^
**Type:** ``int``

**Description:** Right indentation in twips

**Example:**

.. code-block:: python

   "paragraph": {
       "right_indent": 720
   }

first_line_indent
^^^^^^^^^^^^^^^^^
**Type:** ``int``

**Description:** First line indentation in twips

**Example:**

.. code-block:: python

   "paragraph": {
       "first_line_indent": 360  # 0.25 inch
   }

Visual Effects
~~~~~~~~~~~~~~

shading
^^^^^^^
**Type:** ``str`` or ``dict``

**Description:** Background color/shading for paragraph

**Example:**

.. code-block:: python

   "paragraph": {
       "shading": "FFFF00"  # Yellow background
   }

   "paragraph": {
       "shading": {
           "fill": "E7E6E6"  # Light gray
       }
   }

**Common values:**

* ``"FFFF00"`` - Yellow
* ``"E7E6E6"`` - Light gray
* ``"D9D9D9"`` - Medium gray
* ``"C0C0C0"`` - Silver

borders
^^^^^^^
**Type:** ``dict``

**Description:** Paragraph borders configuration

**Example:**

.. code-block:: python

   "paragraph": {
       "borders": {
           "bottom": {
               "color": "000000",  # Black
               "size": 6,          # 0.75 points
               "style": "single"   # Line style
           },
           "top": {
               "color": "FF0000",
               "size": 12,
               "style": "double"
           }
       }
   }

**Border sides:**

* ``"top"``
* ``"bottom"``
* ``"left"``
* ``"right"``

**Border properties:**

* ``color`` - Hex color (required)
* ``size`` - Width in eighths of a point (default: 6)
* ``style`` - Line style (default: "single")
* ``space`` - Space between border and text in points (default: 1)

**Border styles:**

* ``"single"`` - Single line
* ``"double"`` - Double line
* ``"dotted"`` - Dotted line
* ``"dashed"`` - Dashed line
* ``"thick"`` - Thick line

List Properties
---------------

List properties define numbering and bullet formatting.

Basic List Properties
~~~~~~~~~~~~~~~~~~~~~

numId
^^^^^
**Type:** ``str``

**Description:** Numbering definition ID

**Example:**

.. code-block:: python

   "list": {
       "numId": "1"
   }

ilvl
^^^^
**Type:** ``str``

**Description:** Indentation level (0-8)

**Example:**

.. code-block:: python

   "list": {
       "ilvl": "0"  # Top level
   }

   "list": {
       "ilvl": "1"  # Second level (indented)
   }

**Supported values:**

* ``"0"`` - Level 1 (no indent)
* ``"1"`` - Level 2
* ``"2"`` - Level 3
* up to ``"8"`` - Level 9

format
^^^^^^
**Type:** ``str``

**Description:** List format type

**Example:**

.. code-block:: python

   "list": {
       "format": "bullet"
   }

**Supported values:**

* ``"bullet"`` - Bullet list (•, ○, ▪, etc.)
* ``"decimal"`` - Decimal numbers (1, 2, 3...)
* ``"upperRoman"`` - Upper-case Roman numerals (I, II, III...)
* ``"lowerRoman"`` - Lower-case Roman numerals (i, ii, iii...)
* ``"upperLetter"`` - Upper-case letters (A, B, C...)
* ``"lowerLetter"`` - Lower-case letters (a, b, c...)

lvlText
^^^^^^^
**Type:** ``str``

**Description:** Level text/bullet character

**Example:**

.. code-block:: python

   "list": {
       "lvlText": "•"      # Solid bullet
   }

   "list": {
       "lvlText": "%1."    # Number with period
   }

**Common bullet characters:**

* ``"•"`` - Solid bullet
* ``"○"`` - Hollow bullet
* ``"▪"`` - Square bullet
* ``"▫"`` - Hollow square
* ``"✓"`` - Checkmark
* ``"➢"`` - Arrow

Style Resolution
----------------

Styles are resolved with a priority system that merges multiple sources.

Resolution Order
~~~~~~~~~~~~~~~~

1. **Global defaults** - Document-level defaults
2. **Style ID** - Reference to Word template style
3. **Schema style** - Explicit style from pattern descriptor
4. **Inline overrides** - Direct property overrides

**Example:**

.. code-block:: python

   # 1. Global defaults
   global_defaults = {
       "font": {"name": "Arial", "size": 11},
       "paragraph": {"alignment": "left"}
   }

   # 2. Style from Word template (via style_id)
   style_id = "Heading1"  # Has: font size 16, bold

   # 3. Schema style (overrides)
   schema_style = {
       "font": {"color": "FF0000"}  # Add red color
   }

   # Final resolved style:
   # {
   #   "font": {
   #     "name": "Arial",        # From global defaults
   #     "size": 16,             # From style_id (overrides global)
   #     "bold": True,           # From style_id
   #     "color": "FF0000"       # From schema (highest priority)
   #   },
   #   "paragraph": {
   #     "alignment": "left"     # From global defaults
   #   }
   # }

Deep Merging
~~~~~~~~~~~~

Font and paragraph properties are deep-merged:

.. code-block:: python

   base = {
       "font": {
           "name": "Arial",
           "size": 12
       }
   }

   override = {
       "font": {
           "bold": True,
           "color": "FF0000"
       }
   }

   # Result after deep merge:
   {
       "font": {
           "name": "Arial",        # Preserved from base
           "size": 12,             # Preserved from base
           "bold": True,           # Added from override
           "color": "FF0000"       # Added from override
       }
   }

Common Style Patterns
---------------------

Heading Styles
~~~~~~~~~~~~~~

**Large Bold Heading:**

.. code-block:: python

   {
       "font": {
           "name": "Arial",
           "size": 18,
           "bold": True
       },
       "paragraph": {
           "spacing_before": 480,
           "spacing_after": 240
       }
   }

**Centered Title:**

.. code-block:: python

   {
       "font": {
           "name": "Arial",
           "size": 24,
           "bold": True
       },
       "paragraph": {
           "alignment": "center",
           "spacing_after": 240
       }
   }

Body Text Styles
~~~~~~~~~~~~~~~~

**Standard Body:**

.. code-block:: python

   {
       "font": {
           "name": "Times New Roman",
           "size": 12
       },
       "paragraph": {
           "alignment": "justify",
           "line_spacing": 1.15
       }
   }

**Indented Quote:**

.. code-block:: python

   {
       "font": {
           "italic": True
       },
       "paragraph": {
           "left_indent": 720,
           "right_indent": 720,
           "spacing_before": 120,
           "spacing_after": 120,
           "shading": "E7E6E6"
       }
   }

List Styles
~~~~~~~~~~~

**Bullet List:**

.. code-block:: python

   {
       "list": {
           "numId": "1",
           "ilvl": "0",
           "format": "bullet",
           "lvlText": "•"
       },
       "font": {
           "size": 11
       },
       "paragraph": {
           "spacing_after": 60
       }
   }

**Numbered List:**

.. code-block:: python

   {
       "list": {
           "numId": "2",
           "ilvl": "0",
           "format": "decimal",
           "lvlText": "%1."
       },
       "paragraph": {
           "spacing_after": 60
       }
   }

Special Effects
~~~~~~~~~~~~~~~

**Highlighted Text:**

.. code-block:: python

   {
       "font": {
           "highlight": "yellow",
           "bold": True
       }
   }

**Bordered Callout:**

.. code-block:: python

   {
       "paragraph": {
           "borders": {
               "top": {"color": "0000FF", "size": 12, "style": "double"},
               "bottom": {"color": "0000FF", "size": 12, "style": "double"},
               "left": {"color": "0000FF", "size": 6, "style": "single"},
               "right": {"color": "0000FF", "size": 6, "style": "single"}
           },
           "shading": "E7F3FF",
           "spacing_before": 240,
           "spacing_after": 240
       },
       "font": {
           "bold": True
       }
   }

Using Styles in Schemas
-----------------------

Pattern Descriptor Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   {
       "type": "H-SHORT",
       "features": {
           "text": "Chapter 1: Introduction"
       },
       "style": {
           "style_id": "Heading1",
           "font": {
               "name": "Arial",
               "size": 18,
               "bold": True,
               "color": "2E74B5"
           },
           "paragraph": {
               "spacing_before": 480,
               "spacing_after": 240
           }
       }
   }

Programmatic Style Creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def create_heading_style(level: int, text: str):
       """Create a heading style based on level."""
       sizes = {1: 18, 2: 16, 3: 14, 4: 12}

       return {
           "type": f"H-LEVEL-{level}",
           "features": {"text": text},
           "style": {
               "font": {
                   "name": "Arial",
                   "size": sizes.get(level, 12),
                   "bold": True
               },
               "paragraph": {
                   "spacing_before": 240,
                   "spacing_after": 120
               }
           }
       }

   # Usage
   heading = create_heading_style(1, "Introduction")

Modifying Existing Styles
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from glyph.core.schema import GlyphSchemaBuilder

   # Build schema
   builder = GlyphSchemaBuilder(document_xml_path, docx_extract_dir)
   schema = builder.run()

   # Modify all headings to be blue
   for descriptor in schema["pattern_descriptors"]:
       if descriptor["type"].startswith("H-"):
           descriptor.setdefault("style", {})
           descriptor["style"].setdefault("font", {})
           descriptor["style"]["font"]["color"] = "0000FF"

   # Save modified schema
   import json
   with open("modified_schema.json", "w") as f:
       json.dump(schema, f, indent=2)

Best Practices
--------------

Consistency
~~~~~~~~~~~

1. **Use style IDs** when possible to maintain consistency with Word templates
2. **Define common styles** as constants or configuration
3. **Avoid hardcoding** colors and sizes - use variables

Performance
~~~~~~~~~~~

1. **Reuse styles** instead of creating unique styles for each element
2. **Minimize font changes** within documents
3. **Use style_id references** for template-based styles

Accessibility
~~~~~~~~~~~~~

1. **Use sufficient contrast** for text colors (e.g., avoid light gray on white)
2. **Provide structure** with proper heading levels
3. **Use semantic styles** (Heading1, Heading2) instead of just font sizes

Maintainability
~~~~~~~~~~~~~~~

1. **Document custom styles** with comments
2. **Extract styles** to separate configuration files
3. **Version control** style definitions alongside schemas

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Styles not applying:**

- Verify style_id exists in template document
- Check property names match exactly (case-sensitive)
- Ensure values are correct type (int vs str)

**Fonts not rendering:**

- Confirm font is installed on rendering machine
- Use fallback fonts for cross-platform compatibility
- Test with common system fonts (Arial, Times New Roman)

**Colors not showing:**

- Use 6-character hex codes without # prefix
- Verify color values are strings, not integers
- Check for "auto" or empty string values

**Spacing issues:**

- Remember twips are 1/20 of a point
- Use spacing_before/after, not margin
- Check line_spacing is a multiplier (1.0, 1.5, 2.0)

Debugging Styles
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Print resolved style for debugging
   from glyph.core.schema_runner.resolvers.style_resolver import resolve_style

   descriptor = {
       "type": "PARAGRAPH",
       "style": {
           "font": {"bold": True}
       }
   }

   global_defaults = {
       "font": {"name": "Arial", "size": 12}
   }

   resolved = resolve_style(descriptor, {}, global_defaults, None)
   print(json.dumps(resolved, indent=2))

   # Output shows merged style with all properties
