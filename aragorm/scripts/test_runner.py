#!/usr/bin/env python

"""
Before running the tests, make sure there's a test database created, and run
migrations.

Have options similar to Django, so an existing test database can be used
without re-creating it.

Try and make a py.test plugin ... or piggy back on a standard library one???
"""
import os
import sys
import unittest


def create_test_db():
    pass


def teardown_test_db():
    pass


class TestFoo(unittest.TestCase):
    def test_foo(self):
        self.assertTrue(True)


def main():
    # Create test database
    # unittest.main(
    #     testRunner=unittest.TextTestRunner
    # )
    sys.path.insert(0, os.getcwd())

    testsuite = unittest.TestLoader().discover('./tests')
    unittest.TextTestRunner(verbosity=1).run(testsuite)

    # Teardown test database


if __name__ == '__main__':
    main()
