# Development Scripts

The scripts follow GitHub's ["Scripts to Rule Them All"](https://github.com/github/scripts-to-rule-them-all).

Call them from the root of the project, e.g. `./scripts/lint.sh`.

* `scripts/lint.sh` - Run the automated code linting/formatting tools.
* `scripts/release.sh` - Publish package to PyPI.
* `scripts/tests.sh` - General script to run tests and generate coverage report. It's used in the following scripts.
* `scripts/test-postgres.sh` - Run the test suite with Postgres.
* `scripts/test-sqlite.sh` - Run the test suite with SQLite.
* `scripts/piccolo.sh` - Run the Piccolo CLI on the example project in the `tests` folder.
