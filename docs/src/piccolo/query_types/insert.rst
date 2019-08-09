.. _Insert:

Insert
======

This is used to insert rows into the table.

.. code-block:: python

    >>> Band.insert(Band(name="Pythonistas")).run_sync()
    [{'id': 3}]
