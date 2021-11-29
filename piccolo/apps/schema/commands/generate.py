from __future__ import annotations

import asyncio
import dataclasses
import json
import re
import typing as t
import uuid
from datetime import date, datetime

import black
from typing_extensions import Literal

from piccolo.apps.migrations.auto.serialisation import serialise_params
from piccolo.columns import defaults
from piccolo.columns.base import Column, OnDelete, OnUpdate
from piccolo.columns.column_types import (
    JSON,
    JSONB,
    UUID,
    BigInt,
    Boolean,
    Bytea,
    Date,
    DoublePrecision,
    ForeignKey,
    Integer,
    Interval,
    Numeric,
    Real,
    Serial,
    SmallInt,
    Text,
    Timestamp,
    Timestamptz,
    Varchar,
)
from piccolo.columns.defaults.interval import IntervalCustom
from piccolo.columns.indexes import IndexMethod
from piccolo.engine.finder import engine_finder
from piccolo.engine.postgres import PostgresEngine
from piccolo.table import Table, create_table_class, sort_table_classes
from piccolo.utils.naming import _snake_to_camel

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.engine.base import Engine


class ForeignKeyPlaceholder(Table):
    pass


@dataclasses.dataclass
class ConstraintTable:
    name: str = ""
    schema: str = ""


@dataclasses.dataclass
class RowMeta:
    column_default: str
    column_name: str
    is_nullable: Literal["YES", "NO"]
    table_name: str
    character_maximum_length: t.Optional[int]
    data_type: str
    numeric_precision: t.Optional[t.Union[int, str]]
    numeric_scale: t.Optional[t.Union[int, str]]
    numeric_precision_radix: t.Optional[Literal[2, 10]]

    @classmethod
    def get_column_name_str(cls) -> str:
        return ", ".join(i.name for i in dataclasses.fields(cls))


@dataclasses.dataclass
class Constraint:
    constraint_type: Literal["PRIMARY KEY", "UNIQUE", "FOREIGN KEY", "CHECK"]
    constraint_name: str
    constraint_schema: t.Optional[str] = None
    column_name: t.Optional[str] = None


@dataclasses.dataclass
class TableConstraints:
    """
    All of the constraints for a certain table in the database.
    """

    tablename: str
    constraints: t.List[Constraint]

    def __post_init__(self):
        foreign_key_constraints: t.List[Constraint] = []
        unique_constraints: t.List[Constraint] = []
        primary_key_constraints: t.List[Constraint] = []

        for constraint in self.constraints:
            if constraint.constraint_type == "FOREIGN KEY":
                foreign_key_constraints.append(constraint)
            elif constraint.constraint_type == "PRIMARY KEY":
                primary_key_constraints.append(constraint)
            elif constraint.constraint_type == "UNIQUE":
                unique_constraints.append(constraint)

        self.foreign_key_constraints = foreign_key_constraints
        self.unique_constraints = unique_constraints
        self.primary_key_constraints = primary_key_constraints

    def is_primary_key(self, column_name: str) -> bool:
        return any(
            i.column_name == column_name for i in self.primary_key_constraints
        )

    def is_unique(self, column_name: str) -> bool:
        return any(
            i.column_name == column_name for i in self.unique_constraints
        )

    def is_foreign_key(self, column_name: str) -> bool:
        return any(
            i.column_name == column_name for i in self.foreign_key_constraints
        )

    def get_foreign_key_constraint_name(self, column_name) -> ConstraintTable:
        for i in self.foreign_key_constraints:
            if i.column_name == column_name:
                return ConstraintTable(
                    name=i.constraint_name, schema=i.constraint_schema
                )

        raise ValueError("No matching constraint found")


@dataclasses.dataclass
class Trigger:
    constraint_name: str
    constraint_type: str
    table_name: str
    column_name: str
    on_update: str
    on_delete: Literal[
        "NO ACTION", "RESTRICT", "CASCADE", "SET NULL", "SET_DEFAULT"
    ]
    references_table: str
    references_column: str


@dataclasses.dataclass
class TableTriggers:
    """
    All of the triggers for a certain table in the database.
    """

    tablename: str
    triggers: t.List[Trigger]

    def get_column_triggers(self, column_name: str) -> t.List[Trigger]:
        return [i for i in self.triggers if i.column_name == column_name]

    def get_column_ref_trigger(
        self, column_name: str, references_table: str
    ) -> Trigger:
        for trigger in self.triggers:
            if (
                trigger.column_name == column_name
                and trigger.references_table == references_table
            ):
                return trigger

        raise ValueError("No matching trigger found")


@dataclasses.dataclass
class Index:
    indexname: str
    indexdef: str

    def __post_init__(self):
        """
        An example DDL statement which will be parsed:

        .. code-block:: sql

            CREATE INDEX some_index_name
            ON some_schema.some_table
            USING some_index_type (some_column_name)

        If the column name is the same as a Postgres data type, then Postgres
        wraps the column name in quotes. For example, ``"time"`` instead of
        ``time``.

        """
        pat = re.compile(
            r"""^CREATE[ ](?:(?P<unique>UNIQUE)[ ])?INDEX[ ]\w+?[ ]
                 ON[ ].+?[ ]USING[ ](?P<method>\w+?)[ ]
                 \(\"?(?P<column_name>\w+?\"?)\)""",
            re.VERBOSE,
        )
        groups = re.match(pat, self.indexdef).groupdict()

        self.column_name = groups["column_name"].lstrip('"').rstrip('"')
        self.unique = True if "unique" in groups else False
        self.method = INDEX_METHOD_MAP[groups["method"]]


@dataclasses.dataclass
class TableIndexes:
    """
    All of the indexes for a certain table in the database.
    """

    tablename: str
    indexes: t.List[Index]

    def get_column_index(self, column_name: str) -> t.Optional[Index]:
        for i in self.indexes:
            if i.column_name == column_name:
                return i

        return None


@dataclasses.dataclass
class OutputSchema:
    """
    Represents the schema which will be printed out.
    :param imports:
        e.g. ["from piccolo.table import Table"]
    :param warnings:
        e.g. ["some_table.some_column unrecognised_type"]
    :param tables:
        e.g. ["class MyTable(Table): ..."]
    """

    imports: t.List[str] = dataclasses.field(default_factory=list)
    warnings: t.List[str] = dataclasses.field(default_factory=list)
    tables: t.List[t.Type[Table]] = dataclasses.field(default_factory=list)

    def get_table_with_name(self, tablename: str) -> t.Optional[t.Type[Table]]:
        """
        Used to search for a table by name.
        """
        tablename = _snake_to_camel(tablename)
        try:
            return next(
                table for table in self.tables if table.__name__ == tablename
            )
        except StopIteration:
            return None

    def __radd__(self, value: OutputSchema) -> OutputSchema:
        if isinstance(value, int):
            return self
        value.imports.extend(self.imports)
        value.warnings.extend(self.warnings)
        value.tables.extend(self.tables)
        return value

    def __add__(self, value: OutputSchema) -> OutputSchema:
        self.imports.extend(value.imports)
        self.warnings.extend(value.warnings)
        self.tables.extend(value.tables)
        return self


COLUMN_TYPE_MAP: t.Dict[str, t.Type[Column]] = {
    "bigint": BigInt,
    "boolean": Boolean,
    "bytea": Bytea,
    "character varying": Varchar,
    "date": Date,
    "integer": Integer,
    "interval": Interval,
    "json": JSON,
    "jsonb": JSONB,
    "numeric": Numeric,
    "real": Real,
    "double precision": DoublePrecision,
    "smallint": SmallInt,
    "text": Text,
    "timestamp with time zone": Timestamptz,
    "timestamp without time zone": Timestamp,
    "uuid": UUID,
}

COLUMN_DEFAULT_PARSER = {
    BigInt: re.compile(r"^'?(?P<value>-?[0-9]\d*)'?(?:::bigint)?$"),
    Boolean: re.compile(r"^(?P<value>true|false)$"),
    Bytea: re.compile(r"'(?P<value>.*)'::bytea$"),
    DoublePrecision: re.compile(r"(?P<value>[+-]?(?:[0-9]*[.])?[0-9]+)"),
    Varchar: re.compile(r"^'(?P<value>.*)'::character varying$"),
    Date: re.compile(r"^(?P<value>(?:\d{4}-\d{2}-\d{2})|CURRENT_DATE)$"),
    Integer: re.compile(r"^(?P<value>-?\d+)$"),
    Interval: re.compile(
        r"""^
            (?:')?
            (?:
                (?:(?P<years>\d+)[ ]y(?:ear(?:s)?)?\b)        |
                (?:(?P<months>\d+)[ ]m(?:onth(?:s)?)?\b)      |
                (?:(?P<weeks>\d+)[ ]w(?:eek(?:s)?)?\b)        |
                (?:(?P<days>\d+)[ ]d(?:ay(?:s)?)?\b)          |
                (?:
                    (?:
                        (?:(?P<hours>\d+)[ ]h(?:our(?:s)?)?\b)        |
                        (?:(?P<minutes>\d+)[ ]m(?:inute(?:s)?)?\b)    |
                        (?:(?P<seconds>\d+)[ ]s(?:econd(?:s)?)?\b)
                    )   |
                    (?:
                        (?P<digits>-?\d{2}:\d{2}:\d{2}))?\b)
                    )
                +(?P<direction>ago)?
            (?:'::interval)?
            $""",
        re.X,
    ),
    JSON: re.compile(r"^'(?P<value>.*)'::json$"),
    JSONB: re.compile(r"^'(?P<value>.*)'::jsonb$"),
    Numeric: re.compile(r"(?P<value>\d+)"),
    Real: re.compile(r"^(?P<value>-?[0-9]\d*(?:\.\d+)?)$"),
    SmallInt: re.compile(r"^'?(?P<value>-?[0-9]\d*)'?(?:::integer)?$"),
    Text: re.compile(r"^'(?P<value>.*)'::text$"),
    Timestamp: re.compile(
        r"""^
        (?P<value>
            (?:\d{4}-\d{2}-\d{2}[ ]\d{2}:\d{2}:\d{2})   |
            CURRENT_TIMESTAMP
        )
        $""",
        re.VERBOSE,
    ),
    Timestamptz: re.compile(
        r"""^
            (?P<value>
                (?:\d{4}-\d{2}-\d{2}[ ]\d{2}:\d{2}:\d{2}(?:\.\d+)?-\d{2})     |
                CURRENT_TIMESTAMP
            )
            $""",
        re.VERBOSE,
    ),
    UUID: None,
    Serial: None,
    ForeignKey: None,
}


def get_column_default(
    column_type: t.Type[Column], column_default: str
) -> t.Any:
    pat = COLUMN_DEFAULT_PARSER.get(column_type)

    if pat is None:
        return None
    else:
        match = re.match(pat, column_default)
        if match is not None:
            value = match.groupdict()

            if column_type is Boolean:
                return value["value"] == "true"
            elif column_type is Interval:
                kwargs = {}
                for period in [
                    "years",
                    "months",
                    "weeks",
                    "days",
                    "hours",
                    "minutes",
                    "seconds",
                ]:
                    period_match = value.get(period, 0)
                    if period_match:
                        kwargs[period] = int(period_match)
                digits = value["digits"]
                if digits:
                    kwargs.update(
                        dict(
                            zip(
                                ["hours", "minutes", "seconds"],
                                [int(v) for v in digits.split(":")],
                            )
                        )
                    )

                return IntervalCustom(**kwargs)
            elif column_type is JSON or column_type is JSONB:
                return json.loads(value["value"])
            elif column_type is UUID:
                return uuid.uuid4
            elif column_type is Date:
                return (
                    date.today
                    if value["value"] == "CURRENT_DATE"
                    else defaults.date.DateCustom(
                        *[int(v) for v in value["value"].split("-")]
                    )
                )
            elif column_type is Bytea:
                return value["value"].encode("utf8")
            elif column_type is Timestamp:
                return (
                    datetime.now
                    if value["value"] == "CURRENT_TIMESTAMP"
                    else datetime.fromtimestamp(float(value["value"]))
                )
            elif column_type is Timestamptz:
                return (
                    datetime.now
                    if value["value"] == "CURRENT_TIMESTAMP"
                    else datetime.fromtimestamp(float(value["value"]))
                )
            else:
                return column_type.value_type(value["value"])


INDEX_METHOD_MAP: t.Dict[str, IndexMethod] = {
    "btree": IndexMethod.btree,
    "hash": IndexMethod.hash,
    "gist": IndexMethod.gist,
    "gin": IndexMethod.gin,
}


# 'Indices' seems old-fashioned and obscure in this context.
async def get_indexes(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> TableIndexes:
    """
    Get all of the constraints for a table.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.

    """
    indexes = await table_class.raw(
        (
            "SELECT indexname, indexdef "
            "FROM pg_indexes "
            "WHERE schemaname = {} "
            "AND tablename = {}; "
        ),
        schema_name,
        tablename,
    )

    return TableIndexes(
        tablename=tablename,
        indexes=[Index(**i) for i in indexes],
    )


async def get_fk_triggers(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> TableTriggers:
    """
    Get all of the constraints for a table.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.

    """
    triggers = await table_class.raw(
        (
            "SELECT tc.constraint_name, "
            "       tc.constraint_type, "
            "       tc.table_name, "
            "       kcu.column_name, "
            "       rc.update_rule AS on_update, "
            "       rc.delete_rule AS on_delete, "
            "       ccu.table_name AS references_table, "
            "       ccu.column_name AS references_column "
            "FROM information_schema.table_constraints tc "
            "LEFT JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_catalog = kcu.constraint_catalog "
            "  AND tc.constraint_schema = kcu.constraint_schema "
            "  AND tc.constraint_name = kcu.constraint_name "
            "LEFT JOIN information_schema.referential_constraints rc "
            "  ON tc.constraint_catalog = rc.constraint_catalog "
            "  AND tc.constraint_schema = rc.constraint_schema "
            "  AND tc.constraint_name = rc.constraint_name "
            "LEFT JOIN information_schema.constraint_column_usage ccu "
            "  ON rc.unique_constraint_catalog = ccu.constraint_catalog "
            "  AND rc.unique_constraint_schema = ccu.constraint_schema "
            "  AND rc.unique_constraint_name = ccu.constraint_name "
            "WHERE lower(tc.constraint_type) in ('foreign key')"
            "AND tc.table_schema = {} "
            "AND tc.table_name = {}; "
        ),
        schema_name,
        tablename,
    )
    return TableTriggers(
        tablename=tablename,
        triggers=[Trigger(**i) for i in triggers],
    )


ONDELETE_MAP = {
    "NO ACTION": OnDelete.no_action,
    "RESTRICT": OnDelete.restrict,
    "CASCADE": OnDelete.cascade,
    "SET NULL": OnDelete.set_null,
    "SET DEFAULT": OnDelete.set_default,
}

ONUPDATE_MAP = {
    "NO ACTION": OnUpdate.no_action,
    "RESTRICT": OnUpdate.restrict,
    "CASCADE": OnUpdate.cascade,
    "SET NULL": OnUpdate.set_null,
    "SET DEFAULT": OnUpdate.set_default,
}


async def get_constraints(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> TableConstraints:
    """
    Get all of the constraints for a table.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.
    :param tablename:
        Name of the table.
    :param schema_name:
        Name of the schema.


    """
    constraints = await table_class.raw(
        (
            "SELECT tc.constraint_name, tc.constraint_type, kcu.column_name, tc.constraint_schema "  # noqa: E501
            "FROM information_schema.table_constraints tc "
            "LEFT JOIN information_schema.key_column_usage kcu "
            "ON tc.constraint_name = kcu.constraint_name "
            "WHERE tc.table_schema = {} "
            "AND tc.table_name = {} "
        ),
        schema_name,
        tablename,
    )
    return TableConstraints(
        tablename=tablename,
        constraints=[Constraint(**i) for i in constraints],
    )


async def get_tablenames(
    table_class: t.Type[Table], schema_name: str = "public"
) -> t.List[str]:
    """
    Get the tablenames for the schema.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.
    :param schema_name:
        Name of the schema.
    :returns:
        A list of tablenames for the given schema.

    """
    tablenames: t.List[str] = [
        i["tablename"]
        for i in await table_class.raw(
            (
                "SELECT tablename FROM pg_catalog.pg_tables WHERE "
                "schemaname = {}"
            ),
            schema_name,
        ).run()
    ]
    return tablenames


async def get_table_schema(
    table_class: t.Type[Table], tablename: str, schema_name: str = "public"
) -> t.List[RowMeta]:
    """
    Get the schema from the database.

    :param table_class:
        Any Table subclass - just used to execute raw queries on the database.
    :param tablename:
        The name of the table whose schema we want from the database.
    :param schema_name:
        A Postgres database can have multiple schemas, this is the name of the
        one you're interested in.
    :returns:
        A list, with each item containing information about a column in the
        table.

    """
    row_meta_list = await table_class.raw(
        (
            f"SELECT {RowMeta.get_column_name_str()} FROM "
            "information_schema.columns "
            "WHERE table_schema = {} "
            "AND table_name = {}"
        ),
        schema_name,
        tablename,
    ).run()
    return [RowMeta(**row_meta) for row_meta in row_meta_list]


async def get_foreign_key_reference(
    table_class: t.Type[Table], constraint_name: str, constraint_schema: str
) -> ConstraintTable:
    """
    Retrieve the name of the table that a foreign key is referencing.
    """
    response = await table_class.raw(
        (
            "SELECT table_name, table_schema "
            "FROM information_schema.constraint_column_usage "
            "WHERE constraint_name = {} AND constraint_schema  = {};"
        ),
        constraint_name,
        constraint_schema,
    )
    if len(response) > 0:
        return ConstraintTable(
            name=response[0]["table_name"], schema=response[0]["table_schema"]
        )
    else:
        return ConstraintTable()


def get_table_name(name: str, schema: str) -> str:
    if schema == "public":
        return name
    return f"{schema}.{name}"


async def create_table_class_from_db(
    table_class: t.Type[Table], tablename: str, schema_name: str
) -> OutputSchema:
    indexes = await get_indexes(
        table_class=table_class, tablename=tablename, schema_name=schema_name
    )
    constraints = await get_constraints(
        table_class=table_class, tablename=tablename, schema_name=schema_name
    )
    triggers = await get_fk_triggers(
        table_class=table_class, tablename=tablename, schema_name=schema_name
    )
    table_schema = await get_table_schema(
        table_class=table_class, tablename=tablename, schema_name=schema_name
    )
    output_schema = OutputSchema()
    columns: t.Dict[str, Column] = {}

    for pg_row_meta in table_schema:
        data_type = pg_row_meta.data_type
        column_type = COLUMN_TYPE_MAP.get(data_type, None)
        column_name = pg_row_meta.column_name
        column_default = pg_row_meta.column_default
        if not column_type:
            output_schema.warnings.append(
                f"{tablename}.{column_name} ['{data_type}']"
            )
            column_type = Column

        kwargs: t.Dict[str, t.Any] = {
            "null": pg_row_meta.is_nullable == "YES",
            "unique": constraints.is_unique(column_name=column_name),
        }

        index = indexes.get_column_index(column_name=column_name)
        if index is not None:
            kwargs["index"] = True
            kwargs["index_method"] = index.method

        if constraints.is_primary_key(column_name=column_name):
            kwargs["primary_key"] = True
            if column_type == Integer:
                column_type = Serial

        if constraints.is_foreign_key(column_name=column_name):
            fk_constraint_table = constraints.get_foreign_key_constraint_name(
                column_name=column_name
            )
            column_type = ForeignKey
            constraint_table = await get_foreign_key_reference(
                table_class=table_class,
                constraint_name=fk_constraint_table.name,
                constraint_schema=fk_constraint_table.schema,
            )
            if constraint_table.name:
                referenced_table: t.Union[str, t.Optional[t.Type[Table]]]

                if constraint_table.name == tablename:
                    referenced_output_schema = output_schema
                    referenced_table = "self"
                else:
                    referenced_output_schema = (
                        await create_table_class_from_db(
                            table_class=table_class,
                            tablename=constraint_table.name,
                            schema_name=constraint_table.schema,
                        )
                    )
                    referenced_table = (
                        referenced_output_schema.get_table_with_name(
                            tablename=constraint_table.name
                        )
                    )
                kwargs["references"] = (
                    referenced_table
                    if referenced_table is not None
                    else ForeignKeyPlaceholder
                )

                trigger = triggers.get_column_ref_trigger(
                    column_name, constraint_table.name
                )
                if trigger:
                    kwargs["on_update"] = ONUPDATE_MAP[trigger.on_update]
                    kwargs["on_delete"] = ONDELETE_MAP[trigger.on_delete]

                output_schema = sum(  # type: ignore
                    [output_schema, referenced_output_schema]  # type: ignore
                )  # type: ignore
            else:
                kwargs["references"] = ForeignKeyPlaceholder

        output_schema.imports.append(
            "from piccolo.columns.column_types import " + column_type.__name__
        )

        if column_type is Varchar:
            kwargs["length"] = pg_row_meta.character_maximum_length
        elif isinstance(column_type, Numeric):
            radix = pg_row_meta.numeric_precision_radix
            precision = int(str(pg_row_meta.numeric_precision), radix)
            scale = int(str(pg_row_meta.numeric_scale), radix)
            kwargs["digits"] = (precision, scale)

        if column_default:
            default_value = get_column_default(column_type, column_default)
            if default_value:
                kwargs["default"] = default_value

        column = column_type(**kwargs)

        serialised_params = serialise_params(column._meta.params)
        for extra_import in serialised_params.extra_imports:
            output_schema.imports.append(extra_import.__repr__())

        columns[column_name] = column

    table = create_table_class(
        class_name=_snake_to_camel(tablename),
        class_kwargs={"tablename": get_table_name(tablename, schema_name)},
        class_members=columns,
    )
    output_schema.tables.append(table)
    return output_schema


async def get_output_schema(
    schema_name: str = "public",
    include: t.Optional[t.List[str]] = None,
    exclude: t.Optional[t.List[str]] = None,
    engine: t.Optional[Engine] = None,
) -> OutputSchema:
    """
    :param schema_name:
        Name of the schema.
    :param include:
        Optional list of table names. Only creates the specified tables.
    :param exclude:
        Optional list of table names. excludes the specified tables.
    :param engine:
        The ``Engine`` instance to use for making database queries. If not
        specified, then ``engine_finder`` is used to get the engine from
        ``piccolo_conf.py``.
    :returns:
        OutputSchema
    """
    if engine is None:
        engine = engine_finder()

    if exclude is None:
        exclude = []

    if engine is None:
        raise ValueError(
            "Unable to find the engine - make sure piccolo_conf is on the "
            "path."
        )

    if not isinstance(engine, PostgresEngine):
        raise ValueError(
            "This feature is currently only supported in Postgres."
        )

    class Schema(Table, db=engine):
        """
        Just used for making raw queries on the db.
        """

        pass

    if not include:
        include = await get_tablenames(Schema, schema_name=schema_name)

    table_coroutines = (
        create_table_class_from_db(
            table_class=Schema, tablename=tablename, schema_name=schema_name
        )
        for tablename in include
        if tablename not in exclude
    )
    output_schemas = await asyncio.gather(*table_coroutines)

    # Merge all the output schemas to a single OutputSchema object
    output_schema: OutputSchema = sum(output_schemas)  # type: ignore

    # Sort the tables based on their ForeignKeys.
    output_schema.tables = sort_table_classes(
        sorted(output_schema.tables, key=lambda x: x._meta.tablename)
    )
    output_schema.imports = sorted(list(set(output_schema.imports)))

    return output_schema


# This is currently a beta version, and can be improved. However, having
# something working is still useful for people migrating large schemas to
# Piccolo.
async def generate(schema_name: str = "public"):
    """
    Automatically generates Piccolo Table classes by introspecting the
    database. Please check the generated code in case there are errors.

    """
    output_schema = await get_output_schema(schema_name=schema_name)

    output = output_schema.imports + [
        i._table_str(excluded_params=["choices"]) for i in output_schema.tables
    ]

    if output_schema.warnings:
        warning_str = "\n".join(output_schema.warnings)

        output.append('"""')
        output.append(
            "WARNING: Unrecognised column types, added `Column` as a "
            "placeholder:"
        )
        output.append(warning_str)
        output.append('"""')

    nicely_formatted = black.format_str(
        "\n".join(output), mode=black.FileMode(line_length=79)
    )
    print(nicely_formatted)
