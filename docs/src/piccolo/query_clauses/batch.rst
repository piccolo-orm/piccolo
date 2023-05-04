.. _batch:

batch
=====

You can use ``batch`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Example
-------

By default, a query will return as many rows as you ask it for. The problem is
when you have a table containing millions of rows - you might not want to
load them all into memory at once. To get around this, you can batch the
responses.

.. code-block:: python

    # Returns 100 rows at a time:
    async with await Manager.select().batch(batch_size=100) as batch:
        async for _batch in batch:
            print(_batch)

Node
----

If you're using ``extra_nodes`` with :class:`PostgresEngine <piccolo.engine.postgres.PostgresEngine>`,
you can specify which node to query:

.. code-block:: python

    # Returns 100 rows at a time from read_replica_db
    async with await Manager.select().batch(
        batch_size=100,
        node="read_replica_db",
    ) as batch:
        async for _batch in batch:
            print(_batch)

Synchronous version
-------------------

There's currently no synchronous version. However, it's easy enough to achieve:

.. code-block:: python

    async def get_batch():
        async with await Manager.select().batch(batch_size=100) as batch:
            async for _batch in batch:
                print(_batch)

    from piccolo.utils.sync import run_sync
    run_sync(get_batch())
