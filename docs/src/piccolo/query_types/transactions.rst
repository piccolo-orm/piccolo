.. _Transactions:

Transactions
============

Transactions allow multiple queries to be committed only once successful.

This is useful for things like migrations, where you can't have it fail in an
inbetween state.

-------------------------------------------------------------------------------

Accessing the ``Engine``
------------------------

In the examples below we need to access the database ``Engine``.

Each ``Table`` contains a reference to its ``Engine``, which is the easiest
way to access it. For example, with our ``Band`` table:

.. code-block:: python

    DB = Band._meta.db

-------------------------------------------------------------------------------

Atomic
------

This is useful when you want to programmatically add some queries to the
transaction before running it.

.. code-block:: python

    transaction = DB.atomic()
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

    async with DB.transaction():
        await Manager.create_table()
        await Concert.create_table()

Commit
~~~~~~

The transaction is automatically committed when you exit the context manager.

.. code-block:: python

    async with DB.transaction():
        await query_1
        await query_2
        # Automatically committed if the code reaches here.

You can manually commit it if you prefer:

.. code-block:: python

    async with DB.transaction() as transaction:
        await query_1
        await query_2
        await transaction.commit()
        print('transaction committed!')

Rollback
~~~~~~~~

If an exception is raised within the body of the context manager, then the
transaction is automatically rolled back. The exception is still propagated
though.

Rather than raising an exception, if you want to rollback a transaction
manually you can do so as follows:

.. code-block:: python

    async with DB.transaction() as transaction:
        await Manager.create_table()
        await Band.create_table()
        await transaction.rollback()

-------------------------------------------------------------------------------

Nested transactions
-------------------

Nested transactions aren't supported in Postgres, but we can achieve something
similar using `savepoints <Savepoints>`_.

Nested context managers
~~~~~~~~~~~~~~~~~~~~~~~

If you have nested context managers, for example:

.. code-block:: python

    async with DB.transaction():
        async with DB.transaction():
            ...

By default, the inner context manager does nothing, as we're already inside a
transaction.

You can change this behaviour using ``allow_nested=False``, in which case a
``TransactionError`` is raised if you try creating a transaction when one
already exists.

.. code-block:: python

    async with DB.transaction():
        async with DB.transaction(allow_nested=False):
            # TransactionError('A transaction is already active.')

``transaction_exists``
~~~~~~~~~~~~~~~~~~~~~~

You can check whether your code is currently inside a transaction using the
following:

.. code-block:: python

    >>> DB.transaction_exists()
    True

-------------------------------------------------------------------------------

Savepoints
----------

Postgres supports savepoints, which is a way of partially rolling back a
transaction.

.. code-block:: python

    async with DB.transaction() as transaction:
        await Band.insert(Band(name='Pythonistas'))

        savepoint_1 = await transaction.savepoint()

        await Band.insert(Band(name='Terrible band'))

        # Oops, I made a mistake!
        await savepoint_1.rollback_to()

In the above example, the first query will be committed, but not the second.

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
