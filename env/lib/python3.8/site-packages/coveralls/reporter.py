import logging
import os

from coverage import __version__

try:
    from coverage.exceptions import NoSource
    from coverage.exceptions import NotPython
except ImportError:
    from coverage.misc import NoSource
    from coverage.misc import NotPython

log = logging.getLogger('coveralls.reporter')


class CoverallReporter:
    """Custom coverage.py reporter for coveralls.io."""

    def __init__(self, cov, conf, base_dir='', src_dir=''):
        self.coverage = []
        self.base_dir = self.sanitize_dir(base_dir)
        self.src_dir = self.sanitize_dir(src_dir)
        self.report(cov, conf)

    @staticmethod
    def sanitize_dir(directory):
        if directory:
            directory = directory.replace(os.path.sep, '/')
            if directory[-1] != '/':
                directory += '/'
        return directory

    def report5(self, cov):
        # N.B. this method is 99% copied from the coverage source code;
        # unfortunately, the coverage v5 style of `get_analysis_to_report`
        # errors out entirely if any source file has issues -- which would be a
        # breaking change for us. In the interest of backwards compatibility,
        # I've copied their code here so we can maintain the same `coveralls`
        # API regardless of which `coverage` version is being used.
        #
        # TODO: deprecate the relevant APIs so we can just use the coverage
        # public API directly.
        #
        # from coverage.report import get_analysis_to_report
        # try:
        #     for cu, analyzed in get_analysis_to_report(cov, None):
        #         self.parse_file(cu, analyzed)
        # except NoSource:
        #     # Note that this behavior must necessarily change between
        #     # coverage<5 and coverage>=5, as we are no longer interweaving
        #     # with get_analysis_to_report (a single exception breaks the
        #     # whole loop)
        #     log.warning('No source for at least one file')
        # except NotPython:
        #     # Note that this behavior must necessarily change between
        #     # coverage<5 and coverage>=5, as we are no longer interweaving
        #     # with get_analysis_to_report (a single exception breaks the
        #     # whole loop)
        #     log.warning('A source file is not python')
        # except CoverageException as e:
        #     if str(e) != 'No data to report.':
        #         raise

        from coverage.files import FnmatchMatcher, prep_patterns  # pylint: disable=import-outside-toplevel

        # get_analysis_to_report starts here; changes marked with TODOs
        file_reporters = cov._get_file_reporters(None)  # pylint: disable=W0212
        config = cov.config

        if config.report_include:
            matcher = FnmatchMatcher(prep_patterns(config.report_include))
            file_reporters = [fr for fr in file_reporters
                              if matcher.match(fr.filename)]

        if config.report_omit:
            matcher = FnmatchMatcher(prep_patterns(config.report_omit))
            file_reporters = [fr for fr in file_reporters
                              if not matcher.match(fr.filename)]

        # TODO: deprecate changes
        # if not file_reporters:
        #     raise CoverageException("No data to report.")

        for fr in sorted(file_reporters):
            try:
                analysis = cov._analyze(fr)  # pylint: disable=W0212
            except NoSource:
                if not config.ignore_errors:
                    # TODO: deprecate changes
                    # raise
                    log.warning('No source for %s', fr.filename)
            except NotPython:
                # Only report errors for .py files, and only if we didn't
                # explicitly suppress those errors.
                # NotPython is only raised by PythonFileReporter, which has a
                # should_be_python() method.
                if fr.should_be_python():
                    if config.ignore_errors:
                        msg = "Couldn't parse Python file '{}'".format(
                            fr.filename)
                        cov._warn(msg,  # pylint: disable=W0212
                                  slug='couldnt-parse')
                    else:
                        # TODO: deprecate changes
                        # raise
                        log.warning('Source file is not python %s',
                                    fr.filename)
            else:
                # TODO: deprecate changes (well, this one is fine /shrug)
                # yield (fr, analysis)
                self.parse_file(fr, analysis)

    def report(self, cov, conf, morfs=None):
        """
        Generate a part of json report for coveralls.

        `morfs` is a list of modules or filenames.
        `outfile` is a file object to write the json to.
        """
        # pylint: disable=too-many-branches
        try:
            from coverage.report import Reporter  # pylint: disable=import-outside-toplevel
            self.reporter = Reporter(cov, conf)
        except ImportError:  # coverage >= 5.0
            return self.report5(cov)

        for cu in self.reporter.find_file_reporters(morfs):
            try:
                _fn = self.reporter.coverage._analyze  # pylint: disable=W0212
                analyzed = _fn(cu)
                self.parse_file(cu, analyzed)
            except NoSource:
                if not self.reporter.config.ignore_errors:
                    log.warning('No source for %s', cu.filename)
            except NotPython:
                # Only report errors for .py files, and only if we didn't
                # explicitly suppress those errors.
                if (cu.should_be_python()
                        and not self.reporter.config.ignore_errors):
                    log.warning('Source file is not python %s', cu.filename)

        return self.coverage

    @staticmethod
    def get_hits(line_num, analysis):
        """
        Source file stats for each line.

        * A positive integer if the line is covered, representing the number
          of times the line is hit during the test suite.
        * 0 if the line is not covered by the test suite.
        * null to indicate the line is not relevant to code coverage (it may
          be whitespace or a comment).
        """
        if line_num in analysis.missing:
            return 0

        if line_num not in analysis.statements:
            return None

        return 1

    @staticmethod
    def get_arcs(analysis):
        """
        Hit stats for each branch.

        Returns a flat list where every four values represent a branch:
        1. line-number
        2. block-number (not used)
        3. branch-number
        4. hits (we only get 1/0 from coverage.py)
        """
        if not analysis.has_arcs():
            return None

        if not hasattr(analysis, 'branch_lines'):
            # N.B. switching to the public method analysis.missing_branch_arcs
            # would work for half of what we need, but there doesn't seem to be
            # an equivalent analysis.executed_branch_arcs
            branch_lines = analysis._branch_lines()  # pylint: disable=W0212
        else:
            branch_lines = analysis.branch_lines()

        branches = []

        for l1, l2 in analysis.arcs_executed():
            if l1 in branch_lines:
                branches.extend((l1, 0, abs(l2), 1))

        for l1, l2 in analysis.arcs_missing():
            if l1 in branch_lines:
                branches.extend((l1, 0, abs(l2), 0))

        return branches

    def parse_file(self, cu, analysis):
        """Generate data for single file."""
        filename = cu.relative_filename()

        # ensure results are properly merged between platforms
        posix_filename = filename.replace(os.path.sep, '/')

        if self.base_dir and posix_filename.startswith(self.base_dir):
            posix_filename = posix_filename[len(self.base_dir):]
        posix_filename = self.src_dir + posix_filename

        source = analysis.file_reporter.source()

        token_lines = analysis.file_reporter.source_token_lines()
        coverage_lines = [self.get_hits(i, analysis)
                          for i, _ in enumerate(token_lines, 1)]

        results = {
            'name': posix_filename,
            'source': source,
            'coverage': coverage_lines,
        }

        branches = self.get_arcs(analysis)
        if branches:
            results['branches'] = branches

        self.coverage.append(results)
