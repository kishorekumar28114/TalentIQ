"""Job Matcher Backend Application Package."""

import os
import sys

_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

__version__ = "1.0.0"
