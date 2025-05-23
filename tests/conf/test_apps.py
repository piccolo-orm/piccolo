from __future__ import annotations

import pathlib
import tempfile
from unittest import TestCase

from piccolo.apps.user.tables import BaseUser
from piccolo.conf.apps import (
    AppConfig,
    AppRegistry,
    Finder,
    PiccoloConfUpdater,
    table_finder,
)
from tests.example_apps.mega.tables import MegaTable, SmallTable
from tests.example_apps.music.tables import (
    Band,
    Concert,
    Instrument,
    Manager,
    Poster,
    RecordingStudio,
    Shirt,
    Ticket,
    Venue,
)


class TestAppRegistry(TestCase):
    def test_get_app_config(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        app_config = app_registry.get_app_config(app_name="user")
        self.assertIsInstance(app_config, AppConfig)

    def test_get_table_classes(self):
        app_registry = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
        table_classes = app_registry.get_table_classes(app_name="user")
        self.assertIn(BaseUser, table_classes)

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
    def test_pathlib(self):
        """
        Make sure a ``pathlib.Path`` instance can be passed in as a
        ``migrations_folder_path`` argument.
        """
        config = AppConfig(
            app_name="music", migrations_folder_path=pathlib.Path(__file__)
        )
        self.assertEqual(config.resolved_migrations_folder_path, __file__)

    def test_get_table_with_name(self):
        """
        Register a table, then test retrieving it.
        """
        config = AppConfig(app_name="music", migrations_folder_path="")
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
                "Instrument",
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
                "Instrument",
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
                "Instrument",
                "Manager",
                "RecordingStudio",
                "Shirt",
                "Ticket",
                "Venue",
            ],
        )

    def test_exclude_imported(self):
        """
        Make sure we can excluded imported Tables.
        """
        filtered_tables = table_finder(
            modules=["tests.conf.example"],
            exclude_imported=True,
        )

        self.assertEqual(
            [i.__name__ for i in filtered_tables],
            ["Musician"],
        )

        # Now try without filtering:
        all_tables = table_finder(
            modules=["tests.conf.example"],
            exclude_imported=False,
        )

        self.assertEqual(
            sorted([i.__name__ for i in all_tables]),
            ["BaseUser", "Musician"],
        )


class TestFinder(TestCase):
    def test_get_table_classes(self):
        """
        Make sure ``Table`` classes can be retrieved.
        """
        finder = Finder()

        self.assertListEqual(
            sorted(finder.get_table_classes(), key=lambda i: i.__name__),
            [
                Band,
                Concert,
                Instrument,
                Manager,
                MegaTable,
                Poster,
                RecordingStudio,
                Shirt,
                SmallTable,
                Ticket,
                Venue,
            ],
        )

        self.assertListEqual(
            sorted(
                finder.get_table_classes(include_apps=["music"]),
                key=lambda i: i.__name__,
            ),
            [
                Band,
                Concert,
                Instrument,
                Manager,
                Poster,
                RecordingStudio,
                Shirt,
                Ticket,
                Venue,
            ],
        )

        self.assertListEqual(
            sorted(
                finder.get_table_classes(exclude_apps=["music"]),
                key=lambda i: i.__name__,
            ),
            [
                MegaTable,
                SmallTable,
            ],
        )

        with self.assertRaises(ValueError):
            # You shouldn't be allowed to specify both include and exclude.
            finder.get_table_classes(
                exclude_apps=["music"], include_apps=["mega"]
            )

    def test_sort_app_configs(self):
        """
        Make sure we can sort ``AppConfig`` based on their migration
        dependencies.
        """
        app_config_1 = AppConfig(
            app_name="app_1",
            migrations_folder_path="",
        )

        app_config_1._migration_dependency_app_configs = [
            AppConfig(
                app_name="app_2",
                migrations_folder_path="",
            )
        ]

        app_config_2 = AppConfig(
            app_name="app_2",
            migrations_folder_path="",
        )

        app_config_2._migration_dependency_app_configs = []

        sorted_app_configs = Finder().sort_app_configs(
            [app_config_2, app_config_1]
        )

        self.assertListEqual(
            [i.app_name for i in sorted_app_configs], ["app_2", "app_1"]
        )


class TestPiccoloConfUpdater(TestCase):

    def test_modify_app_registry_src(self):
        """
        Make sure the `piccolo_conf.py` source code can be modified
        successfully.
        """
        updater = PiccoloConfUpdater()

        new_src = updater._modify_app_registry_src(
            src="APP_REGISTRY = AppRegistry(apps=[])",
            app_module="music.piccolo_app",
        )
        self.assertEqual(
            new_src.strip(),
            'APP_REGISTRY = AppRegistry(apps=["music.piccolo_app"])',
        )

    def test_register_app(self):
        """
        Make sure the new contents get written to disk.
        """
        temp_dir = tempfile.gettempdir()
        piccolo_conf_path = pathlib.Path(temp_dir) / "piccolo_conf.py"

        src = "APP_REGISTRY = AppRegistry(apps=[])"

        with open(piccolo_conf_path, "wt") as f:
            f.write(src)

        updater = PiccoloConfUpdater(piccolo_conf_path=str(piccolo_conf_path))
        updater.register_app(app_module="music.piccolo_app")

        with open(piccolo_conf_path) as f:
            contents = f.read().strip()

        self.assertEqual(
            contents, 'APP_REGISTRY = AppRegistry(apps=["music.piccolo_app"])'
        )
