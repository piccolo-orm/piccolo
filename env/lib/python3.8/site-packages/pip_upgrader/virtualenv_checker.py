from __future__ import unicode_literals, print_function
import os
import sys

from colorclass import Color


def is_virtualenv():  # pragma: nocover (this is mocked, cannot be tested)
    if getattr(sys, 'base_prefix', sys.prefix) != sys.prefix:
        return True

    if hasattr(sys, 'real_prefix'):
        return True

    if os.environ.get('VIRTUAL_ENV'):
        return True

    return False


def check_for_virtualenv(options):
    if options.get('--skip-virtualenv-check', False) or options.get('--skip-package-installation', False):
        return  # no check needed

    if not is_virtualenv():
        print(Color("{autoyellow}It seems you haven't activated a virtualenv. \n"
                    "Installing packages directly in the system is not recommended. \n"
                    "{automagenta}Activate your project's virtualenv{/automagenta}, "
                    "or {automagenta}re-run this command {/automagenta}with one of the following options:\n"
                    "--skip-virtualenv-check (install the packages anyway)\n"
                    "--skip-package-installation (don't install any package. just update the requirements file(s))"
                    "{/autoyellow}"))
        raise KeyboardInterrupt()
