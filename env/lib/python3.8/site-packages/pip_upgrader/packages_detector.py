from __future__ import print_function, unicode_literals


class PackagesDetector(object):
    """ Takes list of requirements fies and returns the list of packages from all of them """

    packages = []

    def __init__(self, requirements_files):
        self.packages = []
        self.detect_packages(requirements_files)

    def get_packages(self):
        return self.packages

    def detect_packages(self, requirements_files):
        for filename in requirements_files:
            with open(filename) as fh:
                for line in fh:
                    self._process_req_line(line)

    def _process_req_line(self, line):

        if not line or not line.strip():
            return
        line = line.strip()

        if line.startswith('#'):
            return

        if line.startswith('-f') or line.startswith('--find-links') or \
                line.startswith('-i') or line.startswith('--index-url') or \
                line.startswith('--extra-index-url') or \
                line.startswith('--no-index') or \
                line.startswith('-r') or \
                line.startswith('-Z') or line.startswith('--always-unzip'):
            # private repositories
            return

        if '#' in line:  # inline comment in file
            line = line.split('#')[0].strip()

        self.packages.append(line)
