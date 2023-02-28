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

``transaction_exists``
~~~~~~~~~~~~~~~~~~~~~~

You can check whether your code is currently inside a transaction using the
following:

.. code-block:: python

    >>> Band._meta.db.transaction_exists()
    True

-------------------------------------------------------------------------------

Savepoints
----------

Postgres supports savepoints, which is a way of partially rolling back a
transaction.

.. code-block:: python

    async with Band._meta.db.transaction() as transaction:
        await Band.insert(Band(name='Pythonistas'))

        savepoint_1 = await transaction.savepoint()

        await Band.insert(Band(name='Terrible band'))

        # Oops, I made a mistake!
        await savepoint_1.rollback_to()

Named savepoints
~~~~~~~~~~~~~~~~

By default, we assign a name to the savepoint for you. But you can explicitly
give it a name:

.. code-block:: python

    await transaction.savepoint('my_savepoint')

This means you can rollback to this savepoint at any point just using the name:

.. code-block:: python

    await transaction.rollback_to('my_savepoint')

-------------------------------------------------------------------------------

Transaction types
-----------------

SQLite
~~~~~~

For SQLite you may want to specify the :ref:`transaction type <SQLiteTransactionTypes>`,
as it can have an effect on how well the database handles concurrent requests.
