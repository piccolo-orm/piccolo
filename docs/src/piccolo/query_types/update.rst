.. _Update:

Update
======

This is used to update any rows in the table which match the criteria.

.. code-block:: python

    >>> Band.update({
    >>>     Band.name: 'Pythonistas 2'
    >>> }).where(
    >>>     Band.name == 'Pythonistas'
    >>> ).run_sync()
    []

You can also add / subtract / multiply / divide values:

.. code-block:: python

    # Add 100 to the popularity of each band:
    Band.update({
        Band.popularity: Band.popularity + 100
    }).run_sync()

    # Decrease the popularity of each band by 100.
    Band.update({
        Band.popularity: Band.popularity - 100
    }).run_sync()

    # Multiply the popularity of each band by 10.
    Band.update({
        Band.popularity: Band.popularity * 10
    }).run_sync()

    # Divide the popularity of each band by 10.
    Band.update({
        Band.popularity: Band.popularity / 10
    }).run_sync()

    # You can also use the operators in reverse:
    Band.update({
        Band.popularity: 2000 - Band.popularity
    }).run_sync()


Query clauses
-------------

where
~~~~~

See :ref:`Where`.
