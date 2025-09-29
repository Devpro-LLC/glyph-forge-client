#!/usr/bin/env python3
"""Smoke test for glyph-forge package."""

import pytest
from glyph_forge import test
from glyph_forge import __version__
from glyph_forge.test import test as test_function
from glyph_forge.__init__ import __version__ as package_version
def test_smoke():
    """Smoke test for the package."""
    assert True
def test_version():
    """Test the version of the package."""
    assert __version__ == package_version
def test_test_function():
    """Test the test function."""
    assert test() == "Hello from Glyph Forge!"
    assert test_function() == "Hello from Glyph Forge!"