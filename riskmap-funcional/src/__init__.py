"""
Main source package for the Geopolitical Intelligence System.
"""

__version__ = "1.0.0"
__author__ = "Geopolitical Intelligence Team"
__description__ = "Automated OSINT system for geopolitical intelligence analysis"

# Expose subpackage `utils` as top-level import alias so that
# legacy modules can still use "from utils.* import …" even when
# the project is executed as a package (python -m src.*)
import importlib, sys as _sys
if 'utils' not in _sys.modules:
    _sys.modules['utils'] = importlib.import_module(__name__ + '.utils')
# Alias for data_ingestion so that absolute imports still work
if 'data_ingestion' not in _sys.modules:
    _sys.modules['data_ingestion'] = importlib.import_module(__name__ + '.data_ingestion')
