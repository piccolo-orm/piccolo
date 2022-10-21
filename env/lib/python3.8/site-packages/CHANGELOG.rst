Changelog
=========

0.14.0 (2022-02-27)
-------------------

- Improved robustness of importing implicitly namespaced and
  extension packages (#64)

0.13.0 (2022-02-26)
-------------------

- Improved robustness of determining whether a class is pure Python (#65)

0.12.1 (2022-02-12)
-------------------

- Add helpful link to 'failed to find module' message.

0.12.0 (2022-02-06)
-------------------

- Support ``setup.cfg`` as alternate settings file (#52).

0.11.0 (2022-02-05)
-------------------

- Explicitly prevent ambiguous imports (#51).

0.10.2 (2022-01-30)
-------------------

- Correctly handle case when ``__slots__`` is defined as a single string (#47).

0.10.1 (2022-01-30)
-------------------

- Small improvements to verbose error messages.

0.10.0 (2022-01-29)
-------------------

- Detect duplicate slots (#21).
- Improvements to docs.
- Clarify pre-commit usage (#45).

0.9.0 (2022-01-25)
------------------

- Support specifying the location of settings file with ``--settings`` option.
- Improved verbose error messages.

0.8.0 (2022-01-21)
------------------

- Extension modules are now traversed.
- Small tweaks to documentation.

0.7.2 (2022-01-18)
------------------

- Recommend running as ``python -m slotscheck`` when checking files.
  Update pre-commit hook to reflect this.

0.7.1 (2022-01-18)
------------------

- Add Python 3.6 support

0.7.0 (2022-01-18)
------------------

**Breaking changes**

- Strict imports are now the default
- Include/exclude regex patterns now use partial patch (like mypy, isort do).

**Adjustments**

- Clarifications in documentation
- Pre-commit hook uses verbose mode by default

0.6.0 (2022-01-17)
------------------

**Breaking changes**

- Arguments are now file paths. Use the ``-m/--module`` option to scan modules.

**Features**

- Support use as pre-commit hook.
- Multiple modules or files allowed as input.
- Document the types of slot errors.

0.5.3 (2022-01-14)
------------------

- Fix typo in readme.

0.5.2 (2022-01-14)
------------------

- Fix crash when encountering overlapping slots from multiple classes.

0.5.1 (2022-01-14)
------------------

- Relax ``tomli`` dependency pin.

0.5.0 (2022-01-14)
------------------

- More descriptive output on overlapping slots (#26).
- Simplify slot requirement flags.
- allow configuration by ``pyproject.toml`` (#28).

0.4.0 (2022-01-12)
------------------

- Recognize builtin exceptions as not having slots.
- Split ``--exclude-modules`` and ``exclude-classes``.
- Add flags to specify inclusion as well as exclusion of modules/classes.
- Allow disabling slot inheritance check.
- Add ``--require-slots`` option.

0.3.1 (2022-01-10)
------------------

- Catch ``BaseException`` in module import.

0.3.0 (2022-01-10)
------------------

- Add ``--strict-imports`` flag (#24)
- Detect overlapping slots (#10)
- 100% test coverage (#15)
- Add ``--exclude`` flag (#9)

0.2.1 (2022-01-04)
------------------

- Improved error message if module cannot be found (#18)

0.2.0 (2022-01-03)
------------------

- Enable running with ``-m slotscheck`` (#13)

0.1.2 (2022-01-03)
------------------

- Skip ``__main__.py`` in module scan to prevent running unintented code

0.1.1 (2022-01-03)
------------------

- Improve output report

0.1.0 (2020-12-30)
------------------

- Improve documentation

0.0.1 (2021-12-29)
------------------

- Initial release
