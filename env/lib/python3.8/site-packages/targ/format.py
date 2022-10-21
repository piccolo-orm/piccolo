from __future__ import annotations

from enum import Enum

import colorama  # type: ignore

colorama.init()


class Color(Enum):
    white = colorama.Fore.WHITE
    yellow = colorama.Fore.YELLOW
    red = colorama.Fore.RED
    green = colorama.Fore.GREEN
    cyan = colorama.Fore.CYAN


def format_text(message: str, color: Color = Color.white, bold=False) -> str:
    return (
        (colorama.Style.BRIGHT if bold else "")
        + color.value
        + message
        + colorama.Fore.RESET
        + colorama.Style.RESET_ALL
    )


def fixed_width(text: str, min_length: int = 10) -> str:
    length = len(text)
    if length < min_length:
        return text + "".join([" " for _ in range(min_length - length)])
    else:
        return text


def get_underline(length: int, character: str = "=") -> str:
    return "".join([character for i in range(length)])
