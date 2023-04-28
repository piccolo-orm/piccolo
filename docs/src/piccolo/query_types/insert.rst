.. _Insert:

Insert
======

This is used to bulk insert rows into the table:

.. code-block:: python

    await Band.insert(
        Band(name="Pythonistas")
        Band(name="Darts"),
        Band(name="Gophers")
    )

-------------------------------------------------------------------------------

``add``
-------

If we later decide to insert additional rows, we can use the ``add`` method:

.. code-block:: python

    query = Band.insert(Band(name="Pythonistas"))

    if other_bands:
        query = query.add(
            Band(name="Darts"),
            Band(name="Gophers")
        )

    await query

-------------------------------------------------------------------------------

``on_conflict``
---------------

When inserting a row, if a constraint fails (for example, a unique constraint),
then the insertion fails.

Using the ``on_conflict`` clause, we can instead tell the database to ignore
the error (using ``DO NOTHING``), or to update the row (using ``DO UPDATE``).

This is sometimes called an **upsert** (update if it already exists else insert).

Example data
~~~~~~~~~~~~

If we have the following table:

.. code-block:: python

    class Band(Table):
        name = Varchar(unique=True)
        popularity = Integer()

With this data:

.. csv-table::
    :file: ./insert/bands.csv

Let's try inserting another row with the same ``name``, and we'll get an error:

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... )
    Unique constraint error!

``DO NOTHING``
~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~

Instead, if we want to update the ``popularity``:

.. code-block:: python

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO UPDATE",
    ...     values=[Band.popularity]
    ... )

If we fetch the data from the database, we'll see that it was updated:

.. code-block:: python

    >>> await Band.select().where(Band.name == "Pythonistas").first()
    {'id': 1, 'name': 'Pythonistas', 'popularity': 1200}

``target``
~~~~~~~~~~

Using the ``target`` argument, we can specify which constraints we're concerned
with. By specifying ``target=[Band.name]`` we're only concerned with unique
constraints for the ``band`` column. If you omit the ``target`` argument, then
it works for all constraints on the table.

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     target=[Band.name]
    ... )

You can also specify the name of a constraint using a string:

.. code-block:: python
    :emphasize-lines: 5

    >>> await Band.insert(
    ...     Band(name="Pythonistas", popularity=1200)
    ... ).on_conflict(
    ...     action="DO NOTHING",
    ...     target=['some_constraint']
    ... )

``values``
~~~~~~~~~~

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

Source
~~~~~~

.. currentmodule:: piccolo.query.methods.insert

.. automethod:: Insert.on_conflict

.. autoclass:: OnConflictAction
    :members:
    :undoc-members:

-------------------------------------------------------------------------------

Query clauses
-------------

returning
~~~~~~~~~

See :ref:`Returning`.
