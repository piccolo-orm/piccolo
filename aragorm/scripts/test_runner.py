"""
Before running the tests, make sure there's a test database created, and run
migrations.

Have options similar to Django, so an existing test database can be used
without re-creating it.

Try and make a py.test plugin ... or piggy back on a standard library one???
"""
import unittest


def create_test_db():
    pass


def teardown_test_db():
    pass


def main():
    # Create test database
    unittest.main()
    # Teardown test database


if __name__ == '__main__':
    main()
