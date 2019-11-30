from enum import Enum
import warnings

import colorama


colorama.init()


class Level(Enum):
    low = colorama.Fore.WHITE
    medium = colorama.Fore.YELLOW
    high = colorama.Fore.RED


def colored_warning(
    message: str, stacklevel: int = 3, level: Level = Level.medium
):
    colored_message = level.value + message + colorama.Fore.RESET
    warnings.warn(colored_message, stacklevel=stacklevel)
