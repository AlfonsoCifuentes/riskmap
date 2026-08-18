"""
Main source package for the Geopolitical Intelligence System.
"""

__version__ = "1.0.0"
__author__ = "Geopolitical Intelligence Team"
__description__ = "Automated OSINT system for geopolitical intelligence analysis"

# Expose subpackages `utils` / `data_ingestion` as top-level import aliases so
# legacy modules can still use "from utils.* import …" when executed as a
# package (python -m src.*).
#
# These are best-effort: importing a lightweight submodule (e.g. src.core.*)
# must not fail just because an optional heavy dependency of an unrelated
# subpackage (dotenv, collectors, …) is absent. Guard each alias so the base
# package always imports cleanly (addendum: testability of src.core).
import importlib
import sys as _sys

for _alias, _target in (("utils", ".utils"), ("data_ingestion", ".data_ingestion")):
    if _alias not in _sys.modules:
        try:
            _sys.modules[_alias] = importlib.import_module(__name__ + _target)
        except Exception:  # noqa: BLE001 — optional legacy alias, never fatal
            pass
