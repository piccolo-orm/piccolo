.. _lock_rows:

lock_rows
=========

You can use the ``lock_rows`` clause with the following queries:

* :ref:`Objects`
* :ref:`Select`

It returns a query that locks rows until the end of the transaction, generating a ``SELECT ... FOR UPDATE`` SQL statement or similar with other lock strengths.

.. note:: Postgres and CockroachDB only.

-------------------------------------------------------------------------------

Basic Usage
-----------

Basic usage without parameters:

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').lock_rows()

Equivalent to:

.. code-block:: sql

   SELECT ... FOR UPDATE


lock_strength
-------------

The parameter ``lock_strength`` controls the strength of the row lock when performing an operation in PostgreSQL.
The value can be a predefined constant from the ``LockStrength`` enum or one of the following strings (case-insensitive):

* ``UPDATE`` (default): Acquires an exclusive lock on the selected rows, preventing other transactions from modifying or locking them until the current transaction is complete.
* ``NO KEY UPDATE`` (Postgres only): Similar to ``UPDATE``, but allows other transactions to insert or delete rows that do not affect the primary key or unique constraints.
* ``KEY SHARE`` (Postgres only): Permits other transactions to acquire key-share or share locks, allowing non-key modifications while preventing updates or deletes.
* ``SHARE``: Acquires a shared lock, allowing other transactions to read the rows but not modify or lock them.

You can specify a different lock strength:

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').lock_rows('SHARE')

Which is equivalent to:

.. code-block:: sql

   SELECT ... FOR SHARE


nowait
------

If another transaction has already acquired a lock on one or more selected rows, an exception will be raised instead of
waiting for the other transaction to release the lock.

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').lock_rows('UPDATE', nowait=True)


skip_locked
-----------

Ignore locked rows.

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').lock_rows('UPDATE', skip_locked=True)


of
--

By default, if there are many tables in a query (e.g. when joining), all tables will be locked.
Using ``of``, you can specify which tables should be locked.

.. code-block:: python

    await Band.select().where(Band.manager.name == 'Guido').lock_rows('UPDATE', of=(Band, ))

-------------------------------------------------------------------------------

Full example
------------

If we have this table:

.. code-block:: python

  class Concert(Table):
      name = Varchar()
      tickets_available = Integer()

And we want to make sure that ``tickets_available`` never goes below 0, we can
do the following:

.. code-block:: python

  async def book_tickets(ticket_count: int):
      async with Concert._meta.db.transaction():
          concert = await Concert.objects().where(
              Concert.name == "Awesome Concert"
          ).first().lock_rows()

          if concert.tickets_available >= ticket_count:
              await concert.update_self({
                  Concert.tickets_available: Concert.tickets_available - ticket_count
              })
          else:
              raise ValueError("Not enough tickets are available!")

This means that when multiple transactions are running at the same time, it
isn't possible to book more tickets than are available.

-------------------------------------------------------------------------------

Learn more
----------

* `Postgres docs <https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE>`_
* `CockroachDB docs <https://www.cockroachlabs.com/docs/stable/select-for-update#lock-strengths>`_
