.. _Insert:

Insert
======

This is used to insert rows into the table.

.. code-block:: python

    >>> Band.insert(Band(name="Pythonistas")).run_sync()
    [{'id': 3}]

We can insert multiple rows in one go:

.. code-block:: python

    Band.insert(
        Band(name="Darts"),
        Band(name="Gophers")
    ).run_sync()

-------------------------------------------------------------------------------

add
---

You can also compose it as follows:

.. code-block:: python

    Band.insert().add(
        Band(name="Darts")
    ).add(
        Band(name="Gophers")
    ).run_sync()
