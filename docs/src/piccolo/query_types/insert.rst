.. _Insert:

Insert
======

This is used to insert rows into the table.

.. code-block:: python

    >>> await Band.insert(Band(name="Pythonistas"))
    [{'id': 3}]

We can insert multiple rows in one go:

.. code-block:: python

    await Band.insert(
        Band(name="Darts"),
        Band(name="Gophers")
    )

-------------------------------------------------------------------------------

add
---

You can also compose it as follows:

.. code-block:: python

    await Band.insert().add(
        Band(name="Darts")
    ).add(
        Band(name="Gophers")
    )

-------------------------------------------------------------------------------

on_conflict
-----------

You can use the ``on_conflict`` clause in an insert query. 
Piccolo has ``DO_NOTHING`` and ``DO_UPDATE`` clauses:

.. code-block:: python

    from piccolo.query.mixins import OnConflict

    await Band.insert(
        Band(id=1, name="Darts"),
        Band(id=2, name="Gophers"),
        on_conflict=OnConflict.do_nothing
    )
