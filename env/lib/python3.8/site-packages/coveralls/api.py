import codecs
import json
import logging
import os
import random
import re
import sys

import coverage
import requests

from .exception import CoverallsException
from .git import git_info
from .reporter import CoverallReporter


log = logging.getLogger('coveralls.api')

NUMBER_REGEX = re.compile(r'(\d+)$', re.IGNORECASE)


class Coveralls:
    # pylint: disable=too-many-public-methods
    config_filename = '.coveralls.yml'

    def __init__(self, token_required=True, service_name=None, **kwargs):
        """
        Initialize the main Coveralls collection entrypoint.

        * repo_token
          The secret token for your repository, found at the bottom of your
          repository's page on Coveralls.

        * service_name
          The CI service or other environment in which the test suite was run.
          This can be anything, but certain services have special features
          (travis-ci, travis-pro, or coveralls-ruby).

        * [service_job_id]
          A unique identifier of the job on the service specified by
          service_name.
        """
        self._data = None
        self._coveralls_host = 'https://coveralls.io/'
        self._token_required = token_required
        self.config = {}

        self.load_config(kwargs, service_name)
        self.ensure_token()

    def ensure_token(self):
        if self.config.get('repo_token') or not self._token_required:
            return

        if os.environ.get('GITHUB_ACTIONS'):
            raise CoverallsException(
                'Running on Github Actions but GITHUB_TOKEN is not set. '
                'Add "env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}" to '
                'your step config.')

        raise CoverallsException(
            'Not on TravisCI. You have to provide either repo_token in {} or '
            'set the COVERALLS_REPO_TOKEN env var.'.format(
                self.config_filename))

    def load_config(self, kwargs, service_name):
        """
        Loads all coveralls configuration in the following precedence order.

            1. automatic CI configuration
            2. COVERALLS_* env vars
            3. .coveralls.yml config file
            4. CLI flags
        """
        self.load_config_from_ci_environment()
        self.load_config_from_environment()
        self.load_config_from_file()
        self.config.update(kwargs)
        if self.config.get('coveralls_host'):
            # N.B. users can set --coveralls-host via CLI, but we don't keep
            # that in the config
            self._coveralls_host = self.config.pop('coveralls_host')
        if service_name:
            self.config['service_name'] = service_name

    @staticmethod
    def load_config_from_appveyor():
        pr = os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')
        return 'appveyor', os.environ.get('APPVEYOR_BUILD_ID'), None, pr

    @staticmethod
    def load_config_from_buildkite():
        pr = os.environ.get('BUILDKITE_PULL_REQUEST')
        if pr == 'false':
            pr = None
        return 'buildkite', os.environ.get('BUILDKITE_JOB_ID'), None, pr

    @staticmethod
    def load_config_from_circle():
        number = (os.environ.get('CIRCLE_WORKFLOW_ID')
                  or os.environ.get('CIRCLE_BUILD_NUM'))
        pr = (os.environ.get('CI_PULL_REQUEST') or '').split('/')[-1] or None
        job = os.environ.get('CIRCLE_NODE_INDEX')
        return 'circleci', job, number, pr

    def load_config_from_github(self):
        # Github tokens and standard Coveralls tokens are almost but not quite
        # the same -- forceibly using Github's flow seems to be more stable
        self.config['repo_token'] = os.environ.get('GITHUB_TOKEN')

        pr = None
        if os.environ.get('GITHUB_REF', '').startswith('refs/pull/'):
            pr = os.environ.get('GITHUB_REF', '//').split('/')[2]

        # N.B. some users require this to be 'github' and some require it to
        # be 'github-actions'. Defaulting to 'github-actions' as it seems more
        # common -- users can specify the service name manually to override
        # this.
        return 'github-actions', None, os.environ.get('GITHUB_RUN_ID'), pr

    @staticmethod
    def load_config_from_jenkins():
        pr = os.environ.get('CI_PULL_REQUEST', '').split('/')[-1] or None
        return 'jenkins', os.environ.get('BUILD_NUMBER'), None, pr

    @staticmethod
    def load_config_from_travis():
        pr = os.environ.get('TRAVIS_PULL_REQUEST')
        return 'travis-ci', os.environ.get('TRAVIS_JOB_ID'), None, pr

    @staticmethod
    def load_config_from_semaphore():
        job = (
            os.environ.get('SEMAPHORE_JOB_UUID')  # Classic
            or os.environ.get('SEMAPHORE_JOB_ID')  # 2.0
        )
        number = (
            os.environ.get('SEMAPHORE_EXECUTABLE_UUID')  # Classic
            or os.environ.get('SEMAPHORE_WORKFLOW_ID')  # 2.0
        )
        pr = (
            os.environ.get('SEMAPHORE_BRANCH_ID')  # Classic
            or os.environ.get('SEMAPHORE_GIT_PR_NUMBER')  # 2.0
        )
        return 'semaphore-ci', job, number, pr

    @staticmethod
    def load_config_from_unknown():
        return 'coveralls-python', None, None, None

    def load_config_from_generic_ci_environment(self):
        # Inspired by the official client:
        # coveralls-ruby in lib/coveralls/configuration.rb
        # (set_standard_service_params_for_generic_ci)

        # The meaning of each env var is clarified in:
        # https://github.com/lemurheavy/coveralls-public/issues/1558

        config = {
            'service_name': os.environ.get('CI_NAME'),
            'service_number': os.environ.get('CI_BUILD_NUMBER'),
            'service_build_url': os.environ.get('CI_BUILD_URL'),
            'service_job_id': os.environ.get('CI_JOB_ID'),
            'service_branch': os.environ.get('CI_BRANCH'),
        }

        pr_match = NUMBER_REGEX.findall(os.environ.get('CI_PULL_REQUEST', ''))
        if pr_match:
            config['service_pull_request'] = pr_match[-1]

        non_empty = {key: value for key, value in config.items() if value}
        self.config.update(non_empty)

    def load_config_from_ci_environment(self):
        # As defined at the bottom of
        # https://docs.coveralls.io/supported-ci-services
        # there are a few env vars that should support any arbitrary CI.
        # We load them first and allow more specific vars to overwrite
        self.load_config_from_generic_ci_environment()

        if os.environ.get('APPVEYOR'):
            name, job, number, pr = self.load_config_from_appveyor()
        elif os.environ.get('BUILDKITE'):
            name, job, number, pr = self.load_config_from_buildkite()
        elif os.environ.get('CIRCLECI'):
            name, job, number, pr = self.load_config_from_circle()
        elif os.environ.get('GITHUB_ACTIONS'):
            # N.B. Github Actions fails if this is not set even when null.
            # Other services fail if this is set to null. Sigh.
            self.config['service_job_id'] = None
            name, job, number, pr = self.load_config_from_github()
        elif os.environ.get('JENKINS_HOME'):
            name, job, number, pr = self.load_config_from_jenkins()
        elif os.environ.get('TRAVIS'):
            self._token_required = False
            name, job, number, pr = self.load_config_from_travis()
        elif os.environ.get('SEMAPHORE'):
            name, job, number, pr = self.load_config_from_semaphore()
        else:
            name, job, number, pr = self.load_config_from_unknown()

        self.config.setdefault('service_name', name)
        if job:
            self.config['service_job_id'] = job
        if number:
            self.config['service_number'] = number
        if pr:
            self.config['service_pull_request'] = pr

    def load_config_from_environment(self):
        coveralls_host = os.environ.get('COVERALLS_HOST')
        if coveralls_host:
            self._coveralls_host = coveralls_host

        parallel = os.environ.get('COVERALLS_PARALLEL', '').lower() == 'true'
        if parallel:
            self.config['parallel'] = parallel

        fields = {
            'COVERALLS_FLAG_NAME': 'flag_name',
            'COVERALLS_REPO_TOKEN': 'repo_token',
            'COVERALLS_SERVICE_JOB_ID': 'service_job_id',
            'COVERALLS_SERVICE_JOB_NUMBER': 'service_job_number',
            'COVERALLS_SERVICE_NAME': 'service_name',
            'COVERALLS_SERVICE_NUMBER': 'service_number',
        }
        for var, key in fields.items():
            value = os.environ.get(var)
            if value:
                self.config[key] = value

    def load_config_from_file(self):
        try:
            fname = os.path.join(os.getcwd(), self.config_filename)

            with open(fname) as config:
                try:
                    import yaml  # pylint: disable=import-outside-toplevel
                    self.config.update(yaml.safe_load(config))
                except ImportError:
                    log.warning('PyYAML is not installed, skipping %s.',
                                self.config_filename)
        except OSError:
            log.debug('Missing %s file. Using only env variables.',
                      self.config_filename)

    def merge(self, path):
        reader = codecs.getreader('utf-8')
        with open(path, 'rb') as fh:
            extra = json.load(reader(fh))
            self.create_data(extra)

    def wear(self, dry_run=False):
        json_string = self.create_report()
        if dry_run:
            return {}
        return self.submit_report(json_string)

    def submit_report(self, json_string):
        endpoint = '{}/api/v1/jobs'.format(self._coveralls_host.rstrip('/'))
        verify = not bool(os.environ.get('COVERALLS_SKIP_SSL_VERIFY'))
        response = requests.post(endpoint, files={'json_file': json_string},
                                 verify=verify)

        # check and adjust/resubmit if submission looks like it failed due to
        # resubmission (non-unique)
        if response.status_code == 422:
            # attach a random value to ensure uniqueness
            # TODO: an auto-incrementing integer might be easier to reason
            # about if we could fetch the previous value
            # N.B. Github Actions fails if this is not set to null.
            # Other services fail if this is set to null. Sigh x2.
            if os.environ.get('GITHUB_REPOSITORY'):
                new_id = None
            else:
                new_id = '{}-{}'.format(
                    self.config.get('service_job_id', 42),
                    random.randint(0, sys.maxsize))
            print('resubmitting with id {}'.format(new_id))

            self.config['service_job_id'] = new_id
            self._data = None  # force create_report to use updated data
            json_string = self.create_report()

            response = requests.post(endpoint,
                                     files={'json_file': json_string},
                                     verify=verify)

        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise CoverallsException(
                'Could not submit coverage: {}'.format(e)) from e

    # https://docs.coveralls.io/parallel-build-webhook
    def parallel_finish(self):
        payload = {'payload': {'status': 'done'}}

        # required args
        if self.config.get('repo_token'):
            payload['repo_token'] = self.config['repo_token']
        if self.config.get('service_number'):
            payload['payload']['build_num'] = self.config['service_number']

        # service-specific parameters
        if os.environ.get('GITHUB_REPOSITORY'):
            # Github Actions only
            payload['repo_name'] = os.environ.get('GITHUB_REPOSITORY')

        endpoint = '{}/webhook'.format(self._coveralls_host.rstrip('/'))
        verify = not bool(os.environ.get('COVERALLS_SKIP_SSL_VERIFY'))
        response = requests.post(endpoint, json=payload, verify=verify)
        try:
            response.raise_for_status()
            response = response.json()
        except Exception as e:
            raise CoverallsException(
                'Parallel finish failed: {}'.format(e)) from e

        if 'error' in response:
            e = response['error']
            raise CoverallsException('Parallel finish failed: {}'.format(e))

        if 'done' not in response or not response['done']:
            raise CoverallsException('Parallel finish failed')

        return response

    def create_report(self):
        """Generate json dumped report for coveralls api."""
        data = self.create_data()
        try:
            json_string = json.dumps(data)
        except UnicodeDecodeError as e:
            log.error('ERROR: While preparing JSON:', exc_info=e)
            self.debug_bad_encoding(data)
            raise

        log_string = re.sub(r'"repo_token": "(.+?)"',
                            '"repo_token": "[secure]"', json_string)
        log.debug(log_string)
        log.debug('==\nReporting %s files\n==\n', len(data['source_files']))
        for source_file in data['source_files']:
            log.debug('%s - %s/%s', source_file['name'],
                      sum(filter(None, source_file['coverage'])),
                      len(source_file['coverage']))
        return json_string

    def save_report(self, file_path):
        """Write coveralls report to file."""
        try:
            report = self.create_report()
        except coverage.CoverageException as e:
            log.error('Failure to gather coverage:', exc_info=e)
        else:
            with open(file_path, 'w') as report_file:
                report_file.write(report)

    def create_data(self, extra=None):
        r"""
        Generate object for api.

        Example json:
            {
                "service_job_id": "1234567890",
                "service_name": "travis-ci",
                "source_files": [
                    {
                        "name": "example.py",
                        "source": "def four\n  4\nend",
                        "coverage": [null, 1, null]
                    },
                    {
                        "name": "two.py",
                        "source": "def seven\n  eight\n  nine\nend",
                        "coverage": [null, 1, 0, null]
                    }
                ],
                "parallel": True
            }
        """
        if self._data:
            return self._data

        self._data = {'source_files': self.get_coverage()}
        self._data.update(git_info())
        self._data.update(self.config)
        if extra:
            if 'source_files' in extra:
                self._data['source_files'].extend(extra['source_files'])
            else:
                log.warning('No data to be merged; does the json file contain '
                            '"source_files" data?')

        return self._data

    def get_coverage(self):
        config_file = self.config.get('config_file', True)
        workman = coverage.coverage(config_file=config_file)
        workman.load()
        workman.get_data()

        base_dir = self.config.get('base_dir') or ''
        src_dir = self.config.get('src_dir') or ''
        return CoverallReporter(workman, workman.config, base_dir,
                                src_dir).coverage

    @staticmethod
    def debug_bad_encoding(data):
        """Let's try to help user figure out what is at fault."""
        at_fault_files = set()
        for source_file_data in data['source_files']:
            for value in source_file_data.values():
                try:
                    json.dumps(value)
                except UnicodeDecodeError:
                    at_fault_files.add(source_file_data['name'])

        if at_fault_files:
            log.error('HINT: Following files cannot be decoded properly into '
                      'unicode. Check their content: %s',
                      ', '.join(at_fault_files))
