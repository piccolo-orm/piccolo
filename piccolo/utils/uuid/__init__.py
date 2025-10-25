try:
    from uuid import uuid7  # type: ignore
except ImportError:
    # For version < Python 3.14
    from ._uuid_backport import uuid7


__all__ = ("uuid7",)
