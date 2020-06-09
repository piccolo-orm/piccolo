from unittest import TestCase

from piccolo.conf.apps import AppRegistry, AppConfig, table_finder


class TestAppRegistry(TestCase):
    def test_init(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        app_config = app_registry.get_app_config(app_name="user")
        self.assertTrue(isinstance(app_config, AppConfig))


class TestTableFinder(TestCase):
    def test_table_finder(self):
        """
        Should return all Table subclasses.
        """
        tables = table_finder(modules=["tests.example_project.tables"])

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            ["Band", "Concert", "Manager", "Poster", "Ticket", "Venue"],
        )

    def test_include_tags(self):
        """
        Should return all Table subclasses with a matching tag.
        """
        tables = table_finder(
            modules=["tests.example_project.tables"], include_tags=["special"]
        )

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names, ["Poster"],
        )

    def test_exclude_tags(self):
        """
        Should return all Table subclasses without the specified tags.
        """
        tables = table_finder(
            modules=["tests.example_project.tables"], exclude_tags=["special"]
        )

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            ["Band", "Concert", "Manager", "Ticket", "Venue"],
        )
