from __future__ import annotations

from typing import Optional

from piccolo.engine.base import Engine


def engine_finder(module_name: Optional[str] = None) -> Optional[Engine]:
    """
    An example module name is `my_piccolo_conf`.

    The value used is determined by:
    module_name argument > environment variable > default.

    The module must be available on the path, so Python can import it.
    """
    from piccolo.conf.apps import Finder

    return Finder().get_engine(module_name=module_name)
