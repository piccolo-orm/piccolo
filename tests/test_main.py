from unittest import TestCase

from piccolo.main import main


class TestMain(TestCase):
    def test_main(self):
        # Just make sure it runs without raising any errors.
        main()
