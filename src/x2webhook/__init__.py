"""Init function."""

import importlib.metadata

__app_name__ = __package__ if __package__ is not None else "X2Webhook"
__package_name__ = __app_name__.replace("_", " ").title()
try:
    __version__ = importlib.metadata.version(__package__ or __name__)
except Exception:
    __version__ = "Unknown"
