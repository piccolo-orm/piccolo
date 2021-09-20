from unittest import TestCase

from piccolo.apps.user.tables import BaseUser
from piccolo.conf.apps import AppConfig, AppRegistry, table_finder
from tests.example_apps.music.tables import Manager


class TestAppRegistry(TestCase):
    def test_get_app_config(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        app_config = app_registry.get_app_config(app_name="user")
        self.assertTrue(isinstance(app_config, AppConfig))

    def test_get_table_classes(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        table_classes = app_registry.get_table_classes(app_name="user")
        self.assertTrue(BaseUser in table_classes)

        with self.assertRaises(ValueError):
            app_registry.get_table_classes(app_name="Foo")

    def test_duplicate_app_names(self):
        """
        An exception should be if apps with duplicate names are registered.
        """
        with self.assertRaises(ValueError):
            AppRegistry(
                apps=[
                    "piccolo.apps.user.piccolo_app",
                    "piccolo.apps.user.piccolo_app",
                ]
            )

    def test_app_names_not_ending_piccolo_app(self):
        """
        Should automatically add `.piccolo_app` to end.
        """
        AppRegistry(
            apps=[
                "piccolo.apps.user",
            ]
        )

    def test_duplicate_app_names_with_auto_changed(self):
        """
        Make sure duplicate app names are still detected when `piccolo_app`
        is omitted from the end.
        """
        with self.assertRaises(ValueError):
            AppRegistry(
                apps=[
                    "piccolo.apps.user.piccolo_app",
                    "piccolo.apps.user",
                ]
            )

    def test_get_table_with_name(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        table = app_registry.get_table_with_name(
            app_name="user", table_class_name="BaseUser"
        )
        self.assertEqual(table, BaseUser)


class TestAppConfig(TestCase):
    def test_get_table_with_name(self):
        """
        Register a table, then test retrieving it.
        """
        config = AppConfig(app_name="Music", migrations_folder_path="")
        config.register_table(table_class=Manager)
        self.assertEqual(config.get_table_with_name("Manager"), Manager)

        with self.assertRaises(ValueError):
            config.get_table_with_name("Foo")


class TestTableFinder(TestCase):
    def test_table_finder(self):
        """
        Should return all Table subclasses.
        """
        tables = table_finder(modules=["tests.example_apps.music.tables"])

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            [
                "Band",
                "Concert",
                "Manager",
                "Poster",
                "RecordingStudio",
                "Shirt",
                "Ticket",
                "Venue",
            ],
        )

        with self.assertRaises(ImportError):
            table_finder(modules=["foo.bar.baz"])

    def test_table_finder_coercion(self):
        """
        Should convert a string argument to a list.
        """
        tables = table_finder(modules="tests.example_apps.music.tables")

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            [
                "Band",
                "Concert",
                "Manager",
                "Poster",
                "RecordingStudio",
                "Shirt",
                "Ticket",
                "Venue",
            ],
        )

    def test_include_tags(self):
        """
        Should return all Table subclasses with a matching tag.
        """
        tables = table_finder(
            modules=["tests.example_apps.music.tables"],
            include_tags=["special"],
        )

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            ["Poster"],
        )

    def test_exclude_tags(self):
        """
        Should return all Table subclasses without the specified tags.
        """
        tables = table_finder(
            modules=["tests.example_apps.music.tables"],
            exclude_tags=["special"],
        )

        table_class_names = [i.__name__ for i in tables]
        table_class_names.sort()

        self.assertEqual(
            table_class_names,
            [
                "Band",
                "Concert",
                "Manager",
                "RecordingStudio",
                "Shirt",
                "Ticket",
                "Venue",
            ],
        )
