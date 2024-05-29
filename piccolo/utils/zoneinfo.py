try:
    from zoneinfo import ZoneInfo  # type: ignore
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore  # noqa: F401


__all__ = ("ZoneInfo",)
