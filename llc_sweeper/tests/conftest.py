import sys
import os
import pytest

# Add src to sys.path so tests can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
