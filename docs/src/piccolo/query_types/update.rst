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

As well as replacing values with new ones, you can also modify existing values, for
instance by adding to an integer.

-------------------------------------------------------------------------------

Modifying values
----------------

Integer columns
~~~~~~~~~~~~~~~

You can add / subtract / multiply / divide values:

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

Varchar / Text columns
~~~~~~~~~~~~~~~~~~~~~~

You can concatenate values:

.. code-block:: python

    # Append "!!!" to each band name.
    Band.update({
        Band.name: Band.name + "!!!"
    }).run_sync()

    # Concatenate the values in each column:
    Band.update({
        Band.name: Band.name + Band.name
    }).run_sync()

    # Prepend "!!!" to each band name.
    Band.update({
        Band.popularity: "!!!" + Band.popularity
    }).run_sync()


You can currently only combine two values together at a time.

-------------------------------------------------------------------------------

Query clauses
-------------

where
~~~~~

See :ref:`Where`.
