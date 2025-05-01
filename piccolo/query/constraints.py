from piccolo.columns import ForeignKey


async def get_fk_constraint_name(column: ForeignKey) -> str:

    table = column._meta.table

    schema = table._meta.schema or "public"
    table_name = table._meta.tablename
    column_name = column._meta.db_column_name

    constraints = await table.raw(
        """
        SELECT
            kcu1.constraint_name AS fk_constraint_name
        FROM information_schema.referential_constraints AS rc

        INNER JOIN information_schema.key_column_usage AS kcu1
            ON kcu1.constraint_catalog = rc.constraint_catalog
            AND kcu1.constraint_schema = rc.constraint_schema
            AND kcu1.constraint_name = rc.constraint_name

        WHERE
            kcu1.table_schema = {} AND
            kcu1.table_name = {} AND
            kcu1.column_name = {}
        """,
        schema,
        table_name,
        column_name,
    )

    return constraints[0]["fk_constraint_name"]
