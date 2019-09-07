import warnings

import colorama


colorama.init()


def colored_warning(message: str, stacklevel: int = 3):
    colored_message = colorama.Fore.RED + message + colorama.Fore.RESET
    warnings.warn(colored_message, stacklevel=stacklevel)
