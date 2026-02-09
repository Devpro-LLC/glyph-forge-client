Inline Markup Reference
=======================

Glyph offers a Tailwind-inspired inline markup system for styling plaintext content directly. This is an alternative to schema-based styling — instead of defining selectors that match patterns, you embed styling instructions directly in the plaintext.

.. contents:: Quick Navigation
   :local:
   :depth: 2

Overview
--------

Glyph provides **two levels** of inline markup:

1. **Block markup** (``$glyph-{utilities}``) — style entire paragraphs
2. **Inline markup** (``[utilities]text[/]``) — style specific words or phrases within a line

Both can be mixed with schema-based styling. When they overlap, the **cascade** determines which style wins.


Styling Cascade
---------------

When multiple styling sources apply to the same text, the highest priority wins:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │  3. [inline] overrides         ← Highest    │
   │     [bold,color-FF0000]word[/]               │
   ├─────────────────────────────────────────────┤
   │  2. $glyph block styles        ← Medium     │
   │     $glyph-font-size-12-italic               │
   ├─────────────────────────────────────────────┤
   │  1. Schema defaults             ← Lowest    │
   │     global_defaults + selectors              │
   └─────────────────────────────────────────────┘

Inline ``[utilities]text[/]`` overrides always win for the specific text they wrap. The surrounding text retains its block-level or schema-level styling.


Block Markup Syntax
-------------------

Block markup wraps entire paragraphs with a ``$glyph-{utilities}`` opening tag and a bare ``$glyph`` closing tag.

Basic Format
~~~~~~~~~~~~

.. code-block:: text

   $glyph-{utilities}
   Your text content here
   $glyph

.. important::
   Each element **must be on its own line**:

   - Line 1: ``$glyph-{utilities}`` (opening tag alone)
   - Line 2+: Text content
   - Last line: ``$glyph`` (closing tag alone)

   **Never** put the tag and text on the same line.

Examples
~~~~~~~~

**Bold heading:**

.. code-block:: text

   $glyph-bold-font-size-18-color-1F4E78
   Document Title
   $glyph

**Body paragraph with spacing:**

.. code-block:: text

   $glyph-font-size-11-line-spacing-1_5-align-justify
   This is a paragraph of body text with proper spacing and justification.
   $glyph

**Multiple paragraphs in one block** (separated by blank lines):

.. code-block:: text

   $glyph-font-size-11
   First paragraph within this block.

   Second paragraph within this block — same styling applies.
   $glyph

Chaining Utilities
~~~~~~~~~~~~~~~~~~

Utilities are chained with dashes. The parser splits them using known prefixes:

.. code-block:: text

   $glyph-bold-italic-font-size-14-color-FF0000
   Bold italic red 14pt text
   $glyph

For clarity, you can also use **commas** to separate utilities:

.. code-block:: text

   $glyph-space-after-12pt,indent-left-20pt,bold
   Spaced, indented, bold text
   $glyph

Shortcuts
~~~~~~~~~

Predefined utility combinations for common patterns:

.. list-table::
   :header-rows: 1
   :widths: 15 45 40

   * - Shortcut
     - Expands To
     - Usage
   * - ``h1``
     - font-size-24, bold, space-before-12pt, space-after-6pt
     - ``$glyph-h1``
   * - ``h2``
     - font-size-18, bold, space-before-10pt, space-after-4pt
     - ``$glyph-h2``
   * - ``h3``
     - font-size-14, bold, space-before-8pt, space-after-2pt
     - ``$glyph-h3``
   * - ``body``
     - font-size-11, line-spacing-1_5, align-justify
     - ``$glyph-body``
   * - ``code``
     - font-name-courier-new, font-size-10
     - ``$glyph-code``
   * - ``quote``
     - italic, indent-left-36pt, indent-right-36pt
     - ``$glyph-quote``

Shortcuts can be combined with additional utilities:

.. code-block:: text

   $glyph-h1-color-1F4E78-align-center
   Colored Centered Heading
   $glyph


Inline Styling Syntax
---------------------

Inline styling lets you format **specific words or phrases** within a line without wrapping the entire paragraph in a ``$glyph`` block.

Basic Format
~~~~~~~~~~~~

.. code-block:: text

   [utilities]styled text[/]

The opening ``[utilities]`` tag specifies which utilities to apply. The closing ``[/]`` tag ends the styled span.

.. important::
   - Close with bare ``[/]`` — **not** ``[/bold]`` or ``[/italic]``
   - Only **run-scoped** utilities work inline (text formatting, not paragraph layout)
   - Inline tags **cannot be nested** — use comma separation instead

Examples
~~~~~~~~

**Bold a specific word:**

.. code-block:: text

   Please review the [bold]attached[/] document before Friday.

**Color a word:**

.. code-block:: text

   The deadline is [color-FF0000]March 15th[/].

**Multiple utilities (comma-separated):**

.. code-block:: text

   The [bold,color-FF0000]project deadline[/] is tomorrow.

**Multiple inline styles in one paragraph:**

.. code-block:: text

   The [bold]project deadline[/] is [color-FF0000]March 15th[/] and the [italic]budget review[/] is pending.

**Inline styles inside a** ``$glyph`` **block (cascade override):**

.. code-block:: text

   $glyph-font-size-11-color-333333
   This paragraph is 11pt dark gray, but [bold,color-FF0000]this phrase[/] is bold red while [italic]this[/] is just italic.
   $glyph

In the example above, the ``[bold,color-FF0000]`` override applies only to "this phrase". The rest of the paragraph keeps its 11pt dark gray styling from the ``$glyph`` block.

Supported Inline Utilities
~~~~~~~~~~~~~~~~~~~~~~~~~~

Only **run-scoped** (text-level) utilities work inside ``[...]`` tags:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Utility
     - Description
   * - ``bold``
     - Bold text
   * - ``italic``
     - Italic text
   * - ``underline``
     - Underline text
   * - ``strike``
     - Strikethrough text
   * - ``font-size-{N}``
     - Font size in points (e.g., ``font-size-14``)
   * - ``font-name-{family}``
     - Font family (e.g., ``font-name-arial``)
   * - ``color-{RRGGBB}``
     - Text color as hex (e.g., ``color-FF0000``)
   * - ``highlight-{color}``
     - Highlight background (e.g., ``highlight-yellow``)
   * - ``all-caps``
     - Display as ALL CAPITALS
   * - ``small-caps``
     - Display as Small Capitals
   * - ``superscript``
     - Superscript text
   * - ``subscript``
     - Subscript text

.. warning::
   **Paragraph-scoped** utilities like ``align-center``, ``space-after-12pt``, and ``indent-left-36pt`` do **not** work inline. Use a ``$glyph`` block for paragraph-level formatting.


Line Breaks
-----------

Use ``[/br]`` to insert an explicit line break (soft return) within a paragraph. Unlike a blank line (which creates a new paragraph), ``[/br]`` keeps text in the same paragraph.

.. code-block:: text

   John Smith[/br]123 Main Street[/br]New York, NY 10001

This renders as three lines in a single paragraph, sharing the same paragraph styling.

**Inside a** ``$glyph`` **block:**

.. code-block:: text

   $glyph-font-size-11
   John Smith[/br]123 Main Street[/br]New York, NY 10001
   $glyph


When to Use Block vs Inline
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Use Block (``$glyph``)
     - Use Inline (``[utilities]``)
   * - Styling an **entire paragraph**
     - Styling a **word or phrase** within a sentence
   * - Applying paragraph formatting (alignment, spacing, indentation)
     - Adding emphasis without disrupting paragraph flow
   * - Creating structured layouts (rows, sections)
     - Mixing styles within one sentence
   * - ``$glyph-bold-font-size-14``
     - ``[bold]one word[/]``

**Rule of thumb:** If you're styling the whole paragraph, use a ``$glyph`` block. If you're styling part of a sentence, use ``[utilities]text[/]`` inline.


Utilities Reference
-------------------

Run Utilities (Text Formatting)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These utilities work at both the block level (``$glyph-bold``) and inline level (``[bold]text[/]``).

**Emphasis:**

.. code-block:: text

   bold, no-bold, italic, no-italic, underline, no-underline
   underline-single, underline-double, underline-dotted, underline-wave, underline-thick
   strike, double-strike, no-strike

**Font:**

.. code-block:: text

   font-name-{family}     e.g., font-name-arial, font-name-times-new-roman
   font-size-{N}          e.g., font-size-12, font-size-18

**Color & Highlighting:**

.. code-block:: text

   color-{RRGGBB}         e.g., color-FF0000 (red), color-1F4E78 (dark blue)
   highlight-{color}      e.g., highlight-yellow, highlight-green, highlight-none

**Case & Script:**

.. code-block:: text

   all-caps, small-caps, no-caps-transform
   superscript, subscript, no-script

**Effects:**

.. code-block:: text

   hidden, no-hidden, outline, no-outline
   shadow, no-shadow, emboss, no-emboss, imprint, no-imprint

**Character Style:**

.. code-block:: text

   char-style-{slug}      e.g., char-style-emphasis, char-style-strong

Paragraph Utilities (Block Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These utilities only work at block level (``$glyph-{utilities}``), **not** inline.

**Alignment:**

.. code-block:: text

   align-left, align-right, align-center, align-justify, align-distribute

**Spacing:**

.. code-block:: text

   space-before-{N}pt     e.g., space-before-12pt
   space-after-{N}pt      e.g., space-after-6pt
   line-spacing-1_0, line-spacing-1_5, line-spacing-2_0
   line-spacing-pt-{N}    e.g., line-spacing-pt-14

**Indentation:**

.. code-block:: text

   indent-left-{N}pt      e.g., indent-left-36pt
   indent-right-{N}pt     e.g., indent-right-36pt
   indent-first-line-{N}pt
   indent-hanging-{N}pt

**Lists:**

.. code-block:: text

   list-bullet, list-number, list-level-{N}, list-restart

**Pagination:**

.. code-block:: text

   keep-together, no-keep-together
   keep-with-next, no-keep-with-next
   page-break-before, no-page-break-before

**Paragraph Style:**

.. code-block:: text

   para-style-{slug}      e.g., para-style-heading-1, para-style-body-text

Section Utilities (Block Only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Page-level layout. Only work at block level.

.. code-block:: text

   section-orientation-portrait, section-orientation-landscape
   section-size-letter, section-size-legal, section-size-a4
   section-margin-all-{N}in        e.g., section-margin-all-1in
   section-margin-{side}-{N}in     e.g., section-margin-left-1_5in
   layout-col-1, layout-col-2, layout-col-3

Break Utilities
~~~~~~~~~~~~~~~

.. code-block:: text

   page-break       Insert a page break
   line-break       Insert a line break (soft return)
   column-break     Insert a column break


Decimal Notation
----------------

Numeric utilities that accept decimal values use **underscore** (``_``) instead of **period** (``.``):

.. code-block:: text

   1.5 inches → 1_5    e.g., section-margin-all-1_5in
   0.5 inches → 0_5    e.g., cell-pad-0_5
   0.75 inches → 0_75  e.g., section-margin-top-0_75in

.. warning::
   Using a period (``1.5``) instead of underscore (``1_5``) will cause a parse error.


Common Mistakes
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Mistake
     - Wrong
     - Correct
   * - Tag and text on same line
     - ``$glyph-bold Hello $glyph``
     - | ``$glyph-bold``
       | ``Hello``
       | ``$glyph``
   * - Forgetting inline closing tag
     - ``[bold]Important text``
     - ``[bold]Important text[/]``
   * - Utility name in closing tag
     - ``[bold]text[/bold]``
     - ``[bold]text[/]``
   * - Spaces in inline utilities
     - ``[bold, italic]text[/]``
     - ``[bold,italic]text[/]``
   * - Nesting inline tags
     - ``[bold][italic]text[/][/]``
     - ``[bold,italic]text[/]``
   * - Paragraph utility used inline
     - ``[align-center]text[/]``
     - Use ``$glyph-align-center`` block
   * - Placeholder instead of value
     - ``$glyph-font-size-{N}``
     - ``$glyph-font-size-12``
   * - Period in decimal value
     - ``section-margin-all-1.5in``
     - ``section-margin-all-1_5in``


Complete Examples
-----------------

Resume with Mixed Styling
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-bold-font-size-24-align-center
   Jane Smith
   $glyph

   $glyph-align-center-font-size-11-color-666666
   jane.smith@email.com | (555) 123-4567 | New York, NY
   $glyph

   $glyph-bold-font-size-14-color-1F4E78-space-after-6pt
   EXPERIENCE
   $glyph

   $glyph-row-cols-2-row-widths-70-30
   $glyph-cell
   $glyph-bold
   Acme Corporation
   $glyph
   $glyph
   $glyph-cell-cell-align-right
   $glyph-italic
   Jan 2020 - Present
   $glyph
   $glyph
   $glyph

   $glyph-list-bullet
   Led a team of [bold]12 engineers[/] to deliver the [italic]Project Atlas[/] platform
   $glyph

   $glyph-list-bullet
   Reduced deployment time by [bold,color-2E75B5]40%[/] through CI/CD automation
   $glyph

Letter with Inline Emphasis
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-font-size-11-line-spacing-1_5
   Dear Hiring Manager,

   I am writing to express my [bold]strong interest[/] in the [italic]Senior Developer[/] position at your company. With [bold]8 years[/] of experience in full-stack development, I bring expertise in [color-1F4E78]React[/], [color-1F4E78]Python[/], and [color-1F4E78]AWS[/].

   The [highlight-yellow]deadline for applications[/] is [bold,color-FF0000]March 15th[/]. Please find my resume attached.

   Sincerely,[/br]Jane Smith
   $glyph

Address Block with Line Breaks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   $glyph-font-size-11
   Jane Smith[/br]123 Main Street[/br]Suite 200[/br]New York, NY 10001
   $glyph


See Also
--------

- :doc:`how_to_use` - Schema selectors and pattern matching
- :doc:`style_reference` - Complete style property reference for schemas
- :doc:`quickstart` - Get started with Glyph Forge
