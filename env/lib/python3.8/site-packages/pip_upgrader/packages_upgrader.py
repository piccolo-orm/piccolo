from __future__ import print_function, unicode_literals

import os

import subprocess
from subprocess import CalledProcessError

import re
from colorclass import Color


class PackagesUpgrader(object):

    selected_packages = None
    requirements_files = None
    upgraded_packages = None
    dry_run = False

    def __init__(self, selected_packages, requirements_files, options):
        self.selected_packages = selected_packages
        self.requirements_files = requirements_files
        self.upgraded_packages = []
        self.dry_run = options['--dry-run']
        skip_pkg_install = options.get('--skip-package-installation', False)
        if 'PIP_UPGRADER_SKIP_PACKAGE_INSTALLATION' in os.environ:
            skip_pkg_install = True  # pragma: nocover
        self.skip_package_installation = skip_pkg_install

    def do_upgrade(self):
        for package in self.selected_packages:
            self._update_package(package)

        return self.upgraded_packages

    def _update_package(self, package):
        """ Update (install) the package in current environment,
        and if success, also replace version in file """
        try:
            if not self.dry_run and not self.skip_package_installation:  # pragma: nocover
                pinned = '{}=={}'.format(package['name'],
                                         package['latest_version'])
                subprocess.check_call(['pip', 'install', pinned])
            else:
                # dry run has priority in messages
                if self.dry_run:
                    lbl = 'Dry Run'
                else:
                    lbl = "Skip Install"  # pragma: nocover
                print('[{}]: skipping package installation:'.format(lbl),
                      package['name'])
            # update only if installation success
            self._update_requirements_package(package)

        except CalledProcessError:  # pragma: nocover
            print(Color('{{autored}}Failed to install package "{}"{{/autored}}'.format(package['name'])))

    def _update_requirements_package(self, package):
        for filename in set(self.requirements_files):
            lines = []

            # read current lines
            with open(filename, 'r') as frh:
                for line in frh:
                    lines.append(line)

            try:
                # write updates lines
                with open(filename, 'w') as fwh:
                    for line in lines:
                        line = self._maybe_update_line_package(line, package)
                        fwh.write(line)
            except Exception as e:  # pragma: nocover
                # at exception, restore old file
                with open(filename, 'w') as fwh:
                    for line in lines:
                        fwh.write(line)
                raise e

    def _maybe_update_line_package(self, line, package):
        original_line = line
        pattern = r'\b{package}(?:\[\w*\])?=={old_version}\b'.format(
            package=re.escape(package['name']),
            old_version=re.escape(str(package['current_version'])))

        if re.search(pattern, line, flags=re.IGNORECASE):
            line = line.replace(
                '=={}'.format(package['current_version']),
                '=={}'.format(package['latest_version'])
            )

        if line != original_line:
            self.upgraded_packages.append(package)

            if self.dry_run:  # pragma: nocover
                print('[Dry Run]: skipping requirements replacement:',
                      original_line.replace('\n', ''), ' / ',
                      line.replace('\n', ''))
                return original_line
        return line
