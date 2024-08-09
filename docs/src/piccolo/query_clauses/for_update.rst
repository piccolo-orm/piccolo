.. _limit:

for_update
=====

You can use ``for_update`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Returns a query that will lock rows until the end of the transaction, generating a SELECT ... FOR UPDATE SQL statement.

.. note:: Postgres and CockroachDB only.

-------------------------------------------------------------------------------

default
~~~~~~~
To use select for update without extra parameters. All matched rows will be locked until the end of transaction.

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').for_update()


equals to:

.. code-block:: sql

   SELECT ... FOR UPDATE


nowait
~~~~~~~
If another transaction has already acquired a lock on one or more selected rows, the exception will be raised instead of waiting for another transaction


.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').for_update(nowait=True)


skip_locked
~~~~~~~
Ignore locked rows

.. code-block:: python

    await Band.select(Band.name == 'Pythonistas').for_update(skip_locked=True)



of
~~~~~~~
By default, if there are many tables in query (e.x. when joining), all tables will be locked.
with `of` you can specify tables, which should be locked.


.. code-block:: python

    await Band.select().where(Band.manager.name == 'Guido').for_update(of=(Band, ))

