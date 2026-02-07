.. _UsingSQLiteAndAsyncioEffectively:

Using SQLite and asyncio effectively
====================================

When using Piccolo with SQLite, there are some best practices to follow.

asyncio => lots of connections
------------------------------

With asyncio, we can potentially open lots of database connections, and attempt
to perform concurrent database writes.

SQLite doesn't support such concurrent behavior as effectively as Postgres, so
we need to be careful.

One write at a time
~~~~~~~~~~~~~~~~~~~

SQLite can easily support lots of transactions concurrently if they are reading,
but only one write can be performed at a time.

-------------------------------------------------------------------------------

.. _SQLiteTransactionTypes:

Transactions
------------

SQLite has several transaction types, as specified by Piccolo's
``TransactionType`` enum:

.. currentmodule:: piccolo.engine.sqlite

.. autoclass:: TransactionType
    :members:
    :undoc-members:

Which to use?
~~~~~~~~~~~~~

When creating a transaction, Piccolo uses ``DEFERRED`` by default (to be
consistent with SQLite).

This means that the first SQL query executed within the transaction determines
whether it's a **READ** or **WRITE**:

* **READ** - if the first query is a ``SELECT``
* **WRITE** - if the first query is something like an ``INSERT`` / ``UPDATE`` / ``DELETE``

If a transaction starts off with a ``SELECT``, but then tries to perform an ``INSERT`` / ``UPDATE`` / ``DELETE``,
SQLite tries to 'promote' the transaction so it can write.

The problem is, if multiple concurrent connections try doing this at the same time,
SQLite will return a database locked error.

So if you're creating a transaction which you know will perform writes, then
create an ``IMMEDIATE`` transaction:

.. code-block:: python

    from piccolo.engine.sqlite import TransactionType

    async with Band._meta.db.transaction(
        transaction_type=TransactionType.immediate
    ):
        # We perform a SELECT first, but as it's an IMMEDIATE transaction,
        # we can later perform writes without getting a database locked
        # error.
        if not await Band.exists().where(Band.name == 'Pythonistas'):
            await Band.objects().create(name="Pythonistas")

Multiple ``IMMEDIATE`` transactions can exist concurrently - SQLite uses a lock
to make sure only one of them writes at a time.

If your transaction will just be performing ``SELECT`` queries, then just use
the default ``DEFERRED`` transactions - you will get improved performance, as
no locking is involved:

.. code-block:: python

    async with Band._meta.db.transaction():
        bands = await Band.select()
        managers = await Manager.select()

-------------------------------------------------------------------------------

timeout
-------

It's recommended to specify the ``timeout`` argument in :class:`SQLiteEngine <piccolo.engine.sqlite.SQLiteEngine>`.

.. code-block:: python

    DB = SQLiteEngine(timeout=60)

Imagine you have a web app, and each endpoint creates a transaction which runs
multiple queries. With SQLite, only a single write operation can happen at a
time, so if several connections are open, they may be queued for a while.

By increasing ``timeout`` it means that queries are less likely to timeout.

To find out more about ``timeout`` see the Python :func:`sqlite3 docs <sqlite3.connect>`.
