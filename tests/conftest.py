"""
pytest configuration for wallasAPI tests.

Ensures the project root (parent of `wallasAPI/`) is on sys.path so that
`from wallasAPI.xxx import ...` works no matter where pytest is invoked from.
"""
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
