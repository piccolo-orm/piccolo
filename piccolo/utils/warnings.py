from __future__ import annotations

import typing as t
import warnings
from enum import Enum

import colorama  # type: ignore

colorama.init()


class Level(Enum):
    low = colorama.Fore.WHITE
    medium = colorama.Fore.YELLOW
    high = colorama.Fore.RED


def colored_string(message: str, level: Level = Level.medium) -> str:
    return level.value + message + colorama.Fore.RESET


def colored_warning(
    message: str,
    category: t.Type[Warning] = Warning,
    stacklevel: int = 3,
    level: Level = Level.medium,
):
    """
    A wrapper around the stdlib's `warnings.warn`, which colours the output.

    :param message:
        The message to display to the user
    :category:
        `Warning` has several subclasses which may be more appropriate, for
        example `DeprecationWarning`.
    :stacklevel:
        Used to determine the source of the error within the source code.
        See the Python docs for more detail.
        https://docs.python.org/3/library/warnings.html#warnings.warn
    :level:
        Used to determine the colour of the text displayed to the user.
    """
    colored_message = colored_string(message=message, level=level)
    warnings.warn(colored_message, category=category, stacklevel=stacklevel)
