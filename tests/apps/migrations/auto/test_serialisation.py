from unittest import TestCase

from piccolo.apps.migrations.auto.serialisation import serialise_params
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults import DateNow, TimeNow, TimestampNow, UUID4
from piccolo.columns.reference import LazyTableReference


def example_function():
    pass


class TestSerialiseParams(TestCase):
    def test_time(self):
        serialised = serialise_params(params={"default": TimeNow()})
        self.assertEqual(serialised.params["default"].__repr__(), "TimeNow()")
        self.assertTrue(len(serialised.extra_imports) == 1)
        self.assertEqual(
            serialised.extra_imports[0].__str__(),
            "from piccolo.columns.defaults.time import TimeNow",
        )

    def test_date(self):
        serialised = serialise_params(params={"default": DateNow()})
        self.assertEqual(serialised.params["default"].__repr__(), "DateNow()")

    def test_timestamp(self):
        serialised = serialise_params(params={"default": TimestampNow()})
        self.assertTrue(
            serialised.params["default"].__repr__() == "TimestampNow()"
        )

    def test_uuid(self):
        serialised = serialise_params(params={"default": UUID4()})
        self.assertTrue(serialised.params["default"].__repr__() == "UUID4()")

    def test_lazy_table_reference(self):
        # These are equivalent:
        references_list = [
            LazyTableReference(
                table_class_name="Manager", app_name="example_app"
            ),
            LazyTableReference(
                table_class_name="Manager",
                module_path="tests.example_app.tables",
            ),
        ]

        for references in references_list:
            serialised = serialise_params(params={"references": references})
            self.assertTrue(
                serialised.params["references"].__repr__() == "Manager"
            )

            self.assertTrue(len(serialised.extra_imports) == 1)
            self.assertEqual(
                serialised.extra_imports[0].__str__(),
                "from piccolo.table import Table",
            )

            self.assertTrue(len(serialised.extra_definitions) == 1)
            self.assertEqual(
                serialised.extra_definitions[0].__str__(),
                'class Manager(Table, tablename="manager"): pass',
            )

    def test_function(self):
        serialised = serialise_params(params={"default": example_function})
        self.assertTrue(
            serialised.params["default"].__repr__() == "example_function"
        )

        self.assertTrue(len(serialised.extra_imports) == 1)
        self.assertEqual(
            serialised.extra_imports[0].__str__(),
            (
                "from tests.apps.migrations.auto.test_serialisation import "
                "example_function"
            ),
        )

        self.assertTrue(len(serialised.extra_definitions) == 0)

    def test_lambda(self):
        """
        Make sure lambda functions are rejected.
        """
        with self.assertRaises(ValueError) as manager:
            serialise_params(params={"default": lambda x: x + 1})

        self.assertEqual(
            manager.exception.__str__(), "Lambdas can't be serialised"
        )

    def test_builtins(self):
        """
        Make sure builtins can be serialised properly.
        """
        serialised = serialise_params(params={"default": list})
        self.assertTrue(serialised.params["default"].__repr__() == "list")

        self.assertTrue(len(serialised.extra_imports) == 0)

    def test_column_instance(self):
        """
        Make sure Column instances can be serialised properly. An example
        use case is when a `base_column` argument is passed to an `Array`
        column.
        """
        serialised = serialise_params(params={"base_column": Varchar()})

        self.assertEqual(
            serialised.params["base_column"].__repr__(),
            "Varchar(length=255, default='', null=False, primary=False, key=False, unique=False, index=False, index_method=IndexMethod.btree)",  # noqa: E501
        )

        self.assertEqual(
            {i.__repr__() for i in serialised.extra_imports},
            {
                "from piccolo.columns.column_types import Varchar",
                "from piccolo.columns.indexes import IndexMethod",
            },
        )
