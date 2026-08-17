"""Shared pytest fixtures / path setup.

Ensures the repository root is importable so `import api._db` works when the
serverless functions under `api/` are tested outside Vercel.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
