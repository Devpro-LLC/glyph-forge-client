# tests/conftest.py
import sys
import os

# Ensure "src" is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
