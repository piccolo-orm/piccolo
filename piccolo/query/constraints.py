from dataclasses import dataclass

from piccolo.columns import ForeignKey
from piccolo.columns.base import OnDelete, OnUpdate


async def get_fk_constraint_name(column: ForeignKey) -> str:
    """
    Checks what the foreign key constraint is called in the database.
    """

    table = column._meta.table

    if table._meta.db.engine_type == "sqlite":
        # TODO - add the query for SQLite
        raise ValueError("SQLite isn't currently supported.")

    schema = table._meta.schema or "public"
    table_name = table._meta.tablename
    column_name = column._meta.db_column_name

    constraints = await table.raw(
        """
        SELECT
            kcu.constraint_name AS fk_constraint_name
        FROM
            information_schema.referential_constraints AS rc
        INNER JOIN
            information_schema.key_column_usage AS kcu
            ON kcu.constraint_catalog = rc.constraint_catalog
            AND kcu.constraint_schema = rc.constraint_schema
            AND kcu.constraint_name = rc.constraint_name
        WHERE
            kcu.table_schema = {} AND
            kcu.table_name = {} AND
            kcu.column_name = {}
        """,
        schema,
        table_name,
        column_name,
    )

    return constraints[0]["fk_constraint_name"]


@dataclass
class ConstraintRules:
    on_delete: OnDelete
    on_update: OnUpdate


async def get_fk_constraint_rules(column: ForeignKey) -> ConstraintRules:
    """
    Checks the constraint rules for this foreign key in the database.
    """
    table = column._meta.table

    if table._meta.db.engine_type == "sqlite":
        # TODO - add the query for SQLite
        raise ValueError("SQLite isn't currently supported.")

    schema = table._meta.schema or "public"
    table_name = table._meta.tablename
    column_name = column._meta.db_column_name

    constraints = await table.raw(
        """
        SELECT
            kcu.constraint_name,
            kcu.table_name,
            kcu.column_name,
            rc.update_rule,
            rc.delete_rule
        FROM
            information_schema.key_column_usage AS kcu
        INNER JOIN
            information_schema.referential_constraints AS rc
            ON kcu.constraint_name = rc.constraint_name
        WHERE
            kcu.table_schema = {} AND
            kcu.table_name = {} AND
            kcu.column_name = {}
        """,
        schema,
        table_name,
        column_name,
    )

    return ConstraintRules(
        on_delete=OnDelete(constraints[0]["delete_rule"]),
        on_update=OnUpdate(constraints[0]["update_rule"]),
    )
