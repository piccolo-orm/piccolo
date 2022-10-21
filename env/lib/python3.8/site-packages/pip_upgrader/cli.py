"""
pip-upgrade

Usage:
  pip-upgrade [<requirements_file>] ... [--prerelease] [-p=<package>...] [--dry-run] [--skip-virtualenv-check] [--skip-package-installation] [--use-default-index]

Arguments:
    requirements_file             The requirement FILE, or WILDCARD PATH to multiple files.
    --prerelease                  Include prerelease versions for upgrade, when querying pypi repositories.
    -p <package>                  Pre-choose which packages tp upgrade. Skips any prompt.
    --dry-run                     Simulates the upgrade, but does not execute the actual upgrade.
    --skip-package-installation   Only upgrade the version in requirements files, don't install the new package.
    --skip-virtualenv-check       Disable virtualenv check. Allows installing the new packages outside the virtualenv.
    --use-default-index           Skip searching for custom index-url in pip configuration file(s).

Examples:
  pip-upgrade             # auto discovers requirements file
  pip-upgrade requirements.txt
  pip-upgrade requirements/dev.txt requirements/production.txt
  pip-upgrade requirements.txt -p django -p celery
  pip-upgrade requirements.txt -p all
  pip-upgrade requirements.txt --dry-run  # run everything as a simulation (don't do the actual upgrade)

Help:
  Interactively upgrade packages from requirements file, and also update the pinned version from requirements file(s).
  If no requirements are given, the command attempts to detect the requirements file(s) in the current directory.

  https://github.com/simion/pip-upgrader
"""  # noqa: E501
from __future__ import print_function, unicode_literals
from colorclass import Windows, Color
from docopt import docopt

from pip_upgrader import __version__ as VERSION
from pip_upgrader.packages_detector import PackagesDetector
from pip_upgrader.packages_interactive_selector import PackageInteractiveSelector
from pip_upgrader.packages_status_detector import PackagesStatusDetector
from pip_upgrader.packages_upgrader import PackagesUpgrader
from pip_upgrader.requirements_detector import RequirementsDetector
from pip_upgrader.virtualenv_checker import check_for_virtualenv


def get_options():
    return docopt(__doc__, version=VERSION)


def main():
    """ Main CLI entrypoint. """
    options = get_options()
    Windows.enable(auto_colors=True, reset_atexit=True)

    try:
        # maybe check if virtualenv is not activated
        check_for_virtualenv(options)

        # 1. detect requirements files
        filenames = RequirementsDetector(options.get('<requirements_file>')).get_filenames()
        if filenames:
            print(Color('{{autoyellow}}Found valid requirements file(s):{{/autoyellow}} '
                        '{{autocyan}}\n{}{{/autocyan}}'.format('\n'.join(filenames))))
        else:  # pragma: nocover
            print(Color('{autoyellow}No requirements files found in current directory. CD into your project '
                        'or manually specify requirements files as arguments.{/autoyellow}'))
            return
        # 2. detect all packages inside requirements
        packages = PackagesDetector(filenames).get_packages()

        # 3. query pypi API, see which package has a newer version vs the one in requirements (or current env)
        packages_status_map = PackagesStatusDetector(
            packages, options.get('--use-default-index')).detect_available_upgrades(options)

        # 4. [optionally], show interactive screen when user can choose which packages to upgrade
        selected_packages = PackageInteractiveSelector(packages_status_map, options).get_packages()

        # 5. having the list of packages, do the actual upgrade and replace the version inside all filenames
        upgraded_packages = PackagesUpgrader(selected_packages, filenames, options).do_upgrade()

        print(Color('{{autogreen}}Successfully upgraded (and updated requirements) for the following packages: '
                    '{}{{/autogreen}}'.format(','.join([package['name'] for package in upgraded_packages]))))
        if options['--dry-run']:
            print(Color('{automagenta}Actually, no, because this was a simulation using --dry-run{/automagenta}'))

    except KeyboardInterrupt:  # pragma: nocover
        print(Color('\n{autored}Upgrade interrupted.{/autored}'))


if __name__ == '__main__':  # pragma: nocover
    main()
