from enum import Enum
from unittest import TestCase

import pytest

from piccolo.apps.migrations.auto.serialisation import (
    CanConflictWithGlobalNames,
    Import,
    UniqueGlobalNameConflictError,
    UniqueGlobalNames,
    serialise_params,
)
from piccolo.columns.base import OnDelete
from piccolo.columns.choices import Choice
from piccolo.columns.column_types import Varchar
from piccolo.columns.defaults import UUID4, DateNow, TimeNow, TimestampNow
from piccolo.columns.reference import LazyTableReference


class TestUniqueGlobals:
    def test_contains_column_types(self):
        assert getattr(UniqueGlobalNames, "COLUMN_VARCHAR", "Varchar")
        assert getattr(UniqueGlobalNames, "COLUMN_SECRET", "Secret")
        assert getattr(UniqueGlobalNames, "COLUMN_TEXT", "Text")
        assert getattr(UniqueGlobalNames, "COLUMN_UUID", "UUID")
        assert getattr(UniqueGlobalNames, "COLUMN_INTEGER", "Integer")
        assert getattr(UniqueGlobalNames, "COLUMN_BIGINT", "BigInt")
        assert getattr(UniqueGlobalNames, "COLUMN_SMALLINT", "SmallInt")
        assert getattr(UniqueGlobalNames, "COLUMN_SERIAL", "Serial")
        assert getattr(UniqueGlobalNames, "COLUMN_BIGSERIAL", "BigSerial")
        assert getattr(UniqueGlobalNames, "COLUMN_PRIMARYKEY", "PrimaryKey")
        assert getattr(UniqueGlobalNames, "COLUMN_TIMESTAMP", "Timestamp")
        assert getattr(UniqueGlobalNames, "COLUMN_TIMESTAMPZ", "Timestampz")
        assert getattr(UniqueGlobalNames, "COLUMN_DATE", "Date")
        assert getattr(UniqueGlobalNames, "COLUMN_TIME", "Time")
        assert getattr(UniqueGlobalNames, "COLUMN_INTERVAL", "Interval")
        assert getattr(UniqueGlobalNames, "COLUMN_BOOLEAN", "Boolean")
        assert getattr(UniqueGlobalNames, "COLUMN_NUMERIC", "Numeric")
        assert getattr(UniqueGlobalNames, "COLUMN_DECIMAL", "Decimal")
        assert getattr(UniqueGlobalNames, "COLUMN_FLOAT", "Float")
        assert getattr(
            UniqueGlobalNames, "COLUMN_DOUBLEPERCISION", "DoublePrecision"
        )
        assert getattr(UniqueGlobalNames, "COLUMN_FOREIGNKEY", "ForeignKey")
        assert getattr(UniqueGlobalNames, "COLUMN_JSON", "JSON")
        assert getattr(UniqueGlobalNames, "COLUMN_BYTEA", "Bytea")
        assert getattr(UniqueGlobalNames, "COLUMN_BLOB", "Blob")
        assert getattr(UniqueGlobalNames, "COLUMN_ARRAY", "Array")

    def test_raise_if_is_conflicting_name(self):
        # Test will fail if this fails
        UniqueGlobalNames.raise_if_is_conflicting_name("SuperMassiveBlackHole")

        with pytest.raises(UniqueGlobalNameConflictError):
            UniqueGlobalNames.raise_if_is_conflicting_name("Varchar")

    def test_is_conflicting_name(self):
        assert (
            UniqueGlobalNames.is_conflicting_name("SuperMassiveBlackHole")
            is False
        )
        assert UniqueGlobalNames.is_conflicting_name("Varchar") is True

    def test_raise_if_are_conflicting_objects(self):
        class ConflictingCls1(CanConflictWithGlobalNames):
            def raise_if_is_conflicting_with_global_name(self):
                pass

        class ConflictingCls2(CanConflictWithGlobalNames):
            def raise_if_is_conflicting_with_global_name(self):
                pass

        class ConflictingCls3(CanConflictWithGlobalNames):
            def raise_if_is_conflicting_with_global_name(self):
                raise UniqueGlobalNameConflictError("test")

        # Test will fail if this fails
        UniqueGlobalNames.raise_if_are_conflicting_objects(
            [ConflictingCls1(), ConflictingCls2()]
        )

        with pytest.raises(UniqueGlobalNameConflictError):
            UniqueGlobalNames.raise_if_are_conflicting_objects(
                [ConflictingCls2(), ConflictingCls3()]
            )


class TestImport:
    def test_with_module_only(self):
        assert repr(Import(module="a.b.c")) == "import a.b.c"

    def test_with_module_and_target(self):
        assert repr(Import(module="a.b", target="c")) == "from a.b import c"

    def test_raise_if_is_conflicting_with_global_name_with_module_only(self):
        # Test will fail if this fails
        Import(module="a.b.c").raise_if_is_conflicting_with_global_name()

        with pytest.raises(UniqueGlobalNameConflictError):
            Import(module="Varchar").raise_if_is_conflicting_with_global_name()

        # Test will fail if this fails
        Import(
            module="Varchar", expect_conflict_with_global_name="Varchar"
        ).raise_if_is_conflicting_with_global_name()

    def test_raise_if_is_conflicting_with_global_name_with_module_and_target(
        self,
    ):
        # Test will fail if this fails
        Import(
            module="a.b", target="c"
        ).raise_if_is_conflicting_with_global_name()

        with pytest.raises(UniqueGlobalNameConflictError):
            Import(
                module="a.b", target="Varchar"
            ).raise_if_is_conflicting_with_global_name()

        # Test will fail if this fails
        Import(
            module="a.b",
            target="Varchar",
            expect_conflict_with_global_name="Varchar",
        ).raise_if_is_conflicting_with_global_name()


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
            LazyTableReference(table_class_name="Manager", app_name="music"),
            LazyTableReference(
                table_class_name="Manager",
                module_path="tests.example_apps.music.tables",
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
                (
                    'class Manager(Table, tablename="manager"): '
                    "id = Serial(null=False, primary_key=True, unique=False, "
                    "index=False, index_method=IndexMethod.btree, "
                    "choices=None, db_column_name='id')"
                ),
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
            "Varchar(length=255, default='', null=False, primary_key=False, unique=False, index=False, index_method=IndexMethod.btree, choices=None, db_column_name=None)",  # noqa: E501
        )

        self.assertEqual(
            {i.__repr__() for i in serialised.extra_imports},
            {
                "from piccolo.columns.column_types import Varchar",
                "from piccolo.columns.indexes import IndexMethod",
            },
        )

    def test_enum_type(self):
        """
        Make sure Enum types can be serialised properly.
        """

        class Choices(Enum):
            a = 1
            b = 2
            c = Choice(value=3, display_name="c1")

        serialised = serialise_params(params={"choices": Choices})

        self.assertEqual(
            serialised.params["choices"].__repr__(),
            "Enum('Choices', {'a': 1, 'b': 2, 'c': Choice(value=3, display_name='c1')})",  # noqa: E501
        )

        self.assertEqual(
            {i.__repr__() for i in serialised.extra_imports},
            {
                "from piccolo.columns.choices import Choice",
                "from enum import Enum",
            },
        )

    def test_custom_enum_instance(self):
        """
        Make sure custom Enum instances can be serialised properly. An example
        is when a user defines a choices Enum, and then sets the default to
        one of those choices.
        """

        class Choices(Enum):
            a = 1
            b = 2

        serialised = serialise_params(params={"default": Choices.a})

        self.assertEqual(serialised.params["default"], 1)
        self.assertEqual(serialised.extra_imports, [])
        self.assertEqual(serialised.extra_definitions, [])

    def test_builtin_enum_instance(self):
        """
        Make sure Enum instances defiend in Piccolo can be serialised properly
        - for example, with on_delete.
        """
        serialised = serialise_params(params={"on_delete": OnDelete.cascade})

        self.assertEqual(
            serialised.params["on_delete"].__repr__(), "OnDelete.cascade"
        )
        self.assertEqual(
            [i.__repr__() for i in serialised.extra_imports],
            ["from piccolo.columns.base import OnDelete"],
        )
        self.assertEqual(serialised.extra_definitions, [])
