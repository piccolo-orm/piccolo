.. _Transactions:

Transactions
============

Transactions allow multiple queries to be committed only once successful.

This is useful for things like migrations, where you can't have it fail in an
inbetween state.

.. note::
    In the examples below we use ``MyTable._meta.db`` to access the ``Engine``,
    which is used to create transactions.

-------------------------------------------------------------------------------

Atomic
------

This is useful when you want to programmatically add some queries to the
transaction before running it.

.. code-block:: python

    transaction = Band._meta.db.atomic()
    transaction.add(Manager.create_table())
    transaction.add(Concert.create_table())
    await transaction.run()

    # You're also able to run this synchronously:
    transaction.run_sync()

-------------------------------------------------------------------------------

Transaction
-----------

This is the preferred way to run transactions - it currently only works with
async.

.. code-block:: python

    async with Band._meta.db.transaction():
        await Manager.create_table()
        await Concert.create_table()

If an exception is raised within the body of the context manager, then the
transaction is automatically rolled back. The exception is still propagated
though.
