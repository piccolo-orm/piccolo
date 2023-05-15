from __future__ import annotations

import abc
import typing as t

from piccolo.engine.base import Engine
from piccolo.engine.finder import engine_finder
from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync


class SchemaDDLBase(abc.ABC):

    db: Engine

    @abc.abstractproperty
    def ddl(self) -> str:
        pass

    def __await__(self):
        return self.run().__await__()

    async def run(self, in_pool=True):
        return await self.db.run_ddl(self.ddl, in_pool=in_pool)

    def run_sync(self, *args, **kwargs):
        return run_sync(self.run(*args, **kwargs))

    def __str__(self) -> str:
        return self.ddl.__str__()


class CreateSchema(SchemaDDLBase):
    def __init__(
        self,
        schema_name: str,
        *,
        if_not_exists: bool,
        db: Engine,
    ):
        self.schema_name = schema_name
        self.if_not_exists = if_not_exists
        self.db = db

    @property
    def ddl(self) -> str:
        query = "CREATE SCHEMA"
        if self.if_not_exists:
            query += " IF NOT EXISTS"
        query += f' "{self.schema_name}"'

        return query


class DropSchema(SchemaDDLBase):
    def __init__(
        self,
        schema_name: str,
        *,
        if_exists: bool,
        cascade: bool,
        db: Engine,
    ):
        self.schema_name = schema_name
        self.if_exists = if_exists
        self.cascade = cascade
        self.db = db

    @property
    def ddl(self) -> str:
        query = "DROP SCHEMA"
        if self.if_exists:
            query += " IF EXISTS"
        query += f' "{self.schema_name}"'

        if self.cascade:
            query += " CASCADE"

        return query


class MoveTable(SchemaDDLBase):
    def __init__(
        self,
        table_name: str,
        new_schema: str,
        db: Engine,
        current_schema: t.Optional[str] = None,
    ):
        self.table_name = table_name
        self.current_schema = current_schema
        self.new_schema = new_schema
        self.db = db

    @property
    def ddl(self):
        table_name = f'"{self.table_name}"'
        if self.current_schema:
            table_name = f'"{self.current_schema}".{table_name}'

        return f'ALTER TABLE {table_name} SET SCHEMA "{self.new_schema}"'


class ListTables:
    def __init__(self, db: Engine, schema_name: str):
        self.db = db
        self.schema_name = schema_name

    async def run(self):
        response = await self.db.run_querystring(
            QueryString(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = {}
                """,
                self.schema_name,
            )
        )
        return [i["table_name"] for i in response]

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class ListSchemas:
    def __init__(self, db: Engine):
        self.db = db

    async def run(self):
        response = await self.db.run_querystring(
            QueryString("SELECT schema_name FROM information_schema.schemata")
        )
        return [i["schema_name"] for i in response]

    def run_sync(self):
        return run_sync(self.run())

    def __await__(self):
        return self.run().__await__()


class SchemaManager:
    def __init__(self, db: t.Optional[Engine] = None):
        """
        :param db:
            Used to execute the database queries. If not specified, we try and
            import it from ``piccolo_conf.py``.
        """
        db = db or engine_finder()

        if not db:
            raise ValueError("The DB can't be found.")

        self.db = db

    def create_schema(
        self, schema_name: str, *, if_not_exists: bool = True
    ) -> CreateSchema:
        return CreateSchema(
            schema_name=schema_name,
            if_not_exists=if_not_exists,
            db=self.db,
        )

    def drop_schema(
        self,
        schema_name: str,
        *,
        if_exists: bool = True,
        cascade: bool = False,
    ) -> DropSchema:
        return DropSchema(
            schema_name=schema_name,
            if_exists=if_exists,
            cascade=cascade,
            db=self.db,
        )

    def move_table(
        self,
        table_name: str,
        new_schema: str,
        current_schema: t.Optional[str] = None,
    ) -> MoveTable:
        """
        Moves a table to a different schema::

            >>> await SchemaManager().move_schema(
            ...     table_name='my_table',
            ...     new_schema='schema_1'
            ... )

        :param table_name:
            The name of the table to move.
        :param new_schema:
            The name of the scheam you want to move the table too.
        :current_schema:
            If not specified, 'public' is assumed.

        """
        return MoveTable(
            table_name=table_name,
            new_schema=new_schema,
            current_schema=current_schema,
            db=self.db,
        )

    def list_tables(self, schema_name: str) -> ListTables:
        return ListTables(db=self.db, schema_name=schema_name)

    def list_schemas(self) -> ListSchemas:
        """
        Returns the name of each schema in the database::

            >>> await SchemaManager().list_schemas()
            ['public', 'schema_1']

        """
        return ListSchemas(db=self.db)
