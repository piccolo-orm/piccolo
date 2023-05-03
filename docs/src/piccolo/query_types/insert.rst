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

Query clauses
-------------

on_conflict
~~~~~~~~~~~

See :ref:`On_Conflict`.


returning
~~~~~~~~~

See :ref:`Returning`.
