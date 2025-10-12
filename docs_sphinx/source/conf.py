# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Glyph Forge'
copyright = '2025, Devpro LLC'
author = 'Devpro LLC'

version = '1.0.0'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx_autodoc_typehints',
    'sphinx_copybutton',
    'myst_parser',
]

# Source file parsers
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True

# MyST parser settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'httpx': ('https://www.python-httpx.org/', None),
}

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_typehints = 'description'
autodoc_typehints_description_target = 'documented'

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']

# Furo theme options
html_theme_options = {
    "light_logo": "logo-light.png",
    "dark_logo": "logo-dark.png",
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "source_repository": "https://github.com/Devpro-LLC/glyph-forge-client",
    "source_branch": "main",
    "source_directory": "docs_sphinx/source/",
    "light_css_variables": {
        "color-brand-primary": "#2962ff",
        "color-brand-content": "#2962ff",
    },
    "dark_css_variables": {
        "color-brand-primary": "#448aff",
        "color-brand-content": "#448aff",
    },
}

# Add any paths that contain custom static files (such as style sheets)
html_css_files = [
    'custom.css',
]

# The name for this set of Sphinx documents
html_title = f"{project} Documentation"

# Add logo if available
# html_logo = "_static/logo.png"

# Add favicon if available
# html_favicon = "_static/favicon.ico"

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# Output file base name for HTML help builder.
htmlhelp_basename = 'GlyphForgedoc'
