import sys


__all__ = ['metadata']


if sys.version_info > (3, 10):
    import importlib.metadata as metadata
else:
    import importlib_metadata as metadata  # type: ignore
