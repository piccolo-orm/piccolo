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
