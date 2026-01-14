.. _on_conflict:

on_conflict
===========

.. hint:: This is an advanced topic, and first time learners of Piccolo
    can skip if they want.

You can use the ``on_conflict`` clause with the following queries:

* :ref:`Insert`

Introduction
------------

When inserting rows into a table, if a unique constraint fails on one or more
of the rows, then the insertion fails.

Using the ``on_conflict`` clause, we can instead tell the database to ignore
the error (using ``DO NOTHING``), or to update the row (using ``DO UPDATE``).

This is sometimes called an **upsert** (update if it already exists else insert).

Example data
------------

If we have the following table:

.. code-block:: python

    class Band(Table):
        name = Varchar(unique=True)
        popularity = Integer()

With this data:

.. csv-table::
    :file: ./on_conflict/bands.csv

Let's try inserting another row with the same ``name``, and we'll get an error:

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... )
    Unique constraint error!

``DO NOTHING``
--------------

To ignore the error:

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING"
    ... )

If we fetch the data from the database, we'll see that it hasn't changed:

.. code-block:: python

    >>> await Band.select().where(Band.name == "Pythonistas").first()
    {'id': 1, 'name': 'Pythonistas', 'popularity': 1000}


``DO UPDATE``
-------------

Instead, if we want to update the ``popularity``:

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     target=Band.name,
    ...     values=[Band.popularity]
    ... )

If we fetch the data from the database, we'll see that it was updated:

.. code-block:: python

    >>> await Band.select().where(Band.name == "Pythonistas").first()
    {'id': 1, 'name': 'Pythonistas', 'popularity': 1200}

``target``
----------

Using the ``target`` argument, we can specify which constraint we're concerned
with. By specifying ``target=Band.name`` we're only concerned with the unique
constraint for the ``band`` column. If you omit the ``target`` argument on
``DO NOTHING`` action, then it works for all constraints on the table. For 
``DO UPDATE`` action, ``target`` is mandatory and must be provided.

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     target=Band.name
    ... )

If you want to target a composite unique constraint, you can do so by passing
in a tuple of columns:

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     target=(Band.name, Band.popularity)
    ... )

You can also specify the name of a constraint using a string:

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     target='some_constraint'
    ... )

.. warning:: Not supported for MySQL.

``values``
----------

This lets us specify which values to update when a conflict occurs.

By specifying a :class:`Column <piccolo.columns.base.Column>`, this means that
the new value for that column will be used:

.. code-block:: python
    :emphasize-lines: 6

    # The new popularity will be 1200.
    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     values=[Band.popularity]
    ... )

Instead, we can specify a custom value using a tuple:

.. code-block:: python
    :emphasize-lines: 6

    # The new popularity will be 1111.
    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     values=[(Band.popularity, 1111)]
    ... )

If we want to update all of the values, we can use :meth:`all_columns<piccolo.table.Table.all_columns>`.

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(id=1, name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     values=Band.all_columns()
    ... )

``where``
---------

This can be used with ``DO UPDATE``. It gives us more control over whether the
update should be made:

.. code-block:: python
    :emphasize-lines: 6

    >>> await Band.insert(
    ...     Band(id=1, name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     values=[Band.popularity],
    ...     where=Band.popularity < 1000
    ... )

.. warning:: Not supported for MySQL. A workaround is possible by using an  
    ``IF`` or ``CASE`` condition in the ``UPDATE`` clause or by first
    performing a separate ``UPDATE``, but this is not currently supported in Piccolo.

Multiple ``on_conflict`` clauses
--------------------------------

SQLite allows you to specify multiple ``ON CONFLICT`` clauses, but Postgres,
Cockroach and MySQL don't.

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     ...
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     ...
    ... )

Learn more
----------

* `Postgres docs <https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT>`_
* `Cockroach docs <https://www.cockroachlabs.com/docs/v2.0/insert.html#on-conflict-clause>`_
* `SQLite docs <https://www.sqlite.org/lang_UPSERT.html>`_
* `MySQL docs <https://dev.mysql.com/doc/refman/8.4/en/insert.html>`_

Source
------

.. currentmodule:: piccolo.query.methods.insert

.. automethod:: Insert.on_conflict

.. autoclass:: OnConflictAction
    :members:
    :undoc-members:
