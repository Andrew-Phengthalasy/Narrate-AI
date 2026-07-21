import sys
import os

# Vercel runs this file from the api/ subdirectory; add the backend root to the
# path so that `main`, `parsers`, and `pipeline` are all importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app  # noqa: F401  – Vercel looks for `app` in this module
