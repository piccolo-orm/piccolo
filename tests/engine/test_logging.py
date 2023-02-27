from unittest.mock import patch

from tests.base import DBTestCase
from tests.example_apps.music.tables import Manager


class TestLogging(DBTestCase):
    def tearDown(self):
        Manager._meta.db.log_queries = False
        Manager._meta.db.log_responses = False
        super().tearDown()

    def test_log_queries(self):
        Manager._meta.db.log_queries = True

        with patch("piccolo.engine.base.Engine.print_query") as print_query:
            Manager.select().run_sync()
            print_query.assert_called_once()

    def test_log_responses(self):
        Manager._meta.db.log_responses = True

        with patch(
            "piccolo.engine.base.Engine.print_response"
        ) as print_response:
            Manager.select().run_sync()
            print_response.assert_called_once()

    def test_log_queries_and_responses(self):
        Manager._meta.db.log_queries = True
        Manager._meta.db.log_responses = True

        with patch("piccolo.engine.base.Engine.print_query") as print_query:
            with patch(
                "piccolo.engine.base.Engine.print_response"
            ) as print_response:
                Manager.select().run_sync()
                print_query.assert_called_once()
                print_response.assert_called_once()
