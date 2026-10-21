.. _with_:

``with_``
=========

You can use the ``with_`` clause with the following queries:

* :ref:`Select`
* :ref:`Update`
* :ref:`Delete`
* :ref:`Insert`

It adds a ``WITH`` clause (a Common Table Expression, or CTE) to the start of
the query. A CTE is a named sub query, which the rest of the query can refer
to.

.. note:: Postgres, CockroachDB and SQLite 3.8.3 or above.

-------------------------------------------------------------------------------

Basic usage
-----------

Create a :class:`CTE <piccolo.query.CTE>` with a name and a body. The body can
be a query, or a :class:`QueryString <piccolo.querystring.QueryString>`.

.. code-block:: python

    from piccolo.query import CTE

    popular = CTE(
        "popular",
        Band.select(Band.id).where(Band.popularity > 1000),
    )

Then pass it to ``with_``. The name of the CTE can now be used in the query,
for example in a sub select:

.. code-block:: python

    >>> from piccolo.querystring import QueryString
    >>> await Concert.select(Concert.id).where(
    ...     Concert.band_1.is_in(QueryString('SELECT "id" FROM "popular"'))
    ... ).with_(popular)

Which is equivalent to:

.. code-block:: sql

    WITH "popular" AS (SELECT ... FROM "band" WHERE "band"."popularity" > 1000)
    SELECT ... FROM "concert" WHERE "concert"."band_1" IN (SELECT "id" FROM "popular")

You can pass in several CTEs, and they're added in the order given. Each one
must have a different name. Later CTEs can refer to earlier ones.

.. code-block:: python

    await Band.select().with_(first_cte, second_cte)

The ``with_`` clause works in the same way with updates, deletes and inserts:

.. code-block:: python

    await Band.update({Band.popularity: 0}).where(
        Band.id.is_in(QueryString('SELECT "id" FROM "popular"'))
    ).with_(popular)

-------------------------------------------------------------------------------

column_names
------------

By default the columns of the CTE are named by its body. You can name them
yourself using ``column_names``. If the body is a ``Select`` query, it must
select the same number of columns.

.. code-block:: python

    popular = CTE(
        "popular",
        Band.select(Band.id, Band.name).where(Band.popularity > 1000),
        column_names=["band_id", "band_name"],
    )

``column_names`` and the CTE name must only contain letters, digits and
underscores, and must not start with a digit. Otherwise a
:class:`CTEError <piccolo.query.CTEError>` is raised.

To refer to the columns, call ``ref`` on the CTE. This returns a
:class:`CTERef <piccolo.query.CTERef>`, which has a ``CTEColumn`` for each of
the column names:

.. code-block:: python

    >>> ref = popular.ref()
    >>> str(ref.band_id)
    '"popular"."band_id"'
    >>> ref.select_all().compile_string()[0]
    'SELECT "popular"."band_id", "popular"."band_name" FROM "popular"'

-------------------------------------------------------------------------------

Recursive CTEs
--------------

A recursive CTE has a base query, and a recursive query which refers to the CTE
itself. They're combined using ``UNION ALL``. ``column_names`` is required.
For example, to find everyone who reports to a particular employee, directly
or indirectly:

.. code-block:: python

    class Employee(Table):
        name = Varchar()
        manager_id = Integer(null=True)

    reports = CTE.recursive(
        "reports",
        base=QueryString(
            'SELECT "id", 0 FROM "employee" WHERE "id" = {}', 2
        ),
        recursive=QueryString(
            'SELECT "employee"."id", "reports"."depth" + 1 '
            'FROM "employee" JOIN "reports" '
            'ON "employee"."manager_id" = "reports"."id"'
        ),
        column_names=["id", "depth"],
    )

    >>> await Employee.select(Employee.name).where(
    ...     Employee.id.is_in(QueryString('SELECT "id" FROM "reports"'))
    ... ).with_(reports)
    [{'name': 'vp'}, {'name': 'lead'}, {'name': 'engineer'}]

If any of the CTEs passed to ``with_`` is recursive, the query starts with
``WITH RECURSIVE``.

-------------------------------------------------------------------------------

materialized
------------

Postgres, CockroachDB and SQLite 3.35 or above let you control whether the result of a CTE is
computed once and stored, using ``MATERIALIZED`` or ``NOT MATERIALIZED``.

.. code-block:: python

    CTE("popular", query, materialized=True)   # AS MATERIALIZED (...)
    CTE("popular", query, materialized=False)  # AS NOT MATERIALIZED (...)
    CTE("popular", query)                      # database decides

-------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.query

.. autoclass:: CTE
    :members: recursive, ref

.. autoclass:: CTERef
    :members: column, columns, from_clause, select_all

.. autoclass:: CTEColumn

.. autoclass:: CTEError
