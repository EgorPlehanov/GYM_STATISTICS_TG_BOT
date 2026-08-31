"""Application configuration entrypoint.

The real settings currently live in the legacy `config_reader` module.
They will be moved here during the backend core refactoring step.
"""

from config_reader import Settings, config

__all__ = ["Settings", "config"]

