.. _Update:

Update
======

This is used to update any rows in the table which match the criteria.

.. code-block:: python

    >>> await Band.update({
    ...     Band.name: 'Pythonistas 2'
    ... }).where(
    ...     Band.name == 'Pythonistas'
    ... )
    []

-------------------------------------------------------------------------------

force
-----

Piccolo won't let you run an update query without a where clause, unless you
explicitly tell it to do so. This is to prevent accidentally overwriting
the data in a table.

.. code-block:: python

    >>> await Band.update()
    Raises: UpdateError

    # Works fine:
    >>> await Band.update({Band.popularity: 0}, force=True)

-------------------------------------------------------------------------------

Modifying values
----------------

As well as replacing values with new ones, you can also modify existing values, for
instance by adding to an integer.

Integer columns
~~~~~~~~~~~~~~~

You can add / subtract / multiply / divide values:

.. code-block:: python

    # Add 100 to the popularity of each band:
    await Band.update({
        Band.popularity: Band.popularity + 100
    })

    # Decrease the popularity of each band by 100.
    await Band.update({
        Band.popularity: Band.popularity - 100
    })

    # Multiply the popularity of each band by 10.
    await Band.update({
        Band.popularity: Band.popularity * 10
    })

    # Divide the popularity of each band by 10.
    await Band.update({
        Band.popularity: Band.popularity / 10
    })

    # You can also use the operators in reverse:
    await Band.update({
        Band.popularity: 2000 - Band.popularity
    })

Varchar / Text columns
~~~~~~~~~~~~~~~~~~~~~~

You can concatenate values:

.. code-block:: python

    # Append "!!!" to each band name.
    await Band.update({
        Band.name: Band.name + "!!!"
    })

    # Concatenate the values in each column:
    await Band.update({
        Band.name: Band.name + Band.name
    })

    # Prepend "!!!" to each band name.
    await Band.update({
        Band.popularity: "!!!" + Band.popularity
    })


You can currently only combine two values together at a time.

-------------------------------------------------------------------------------

Kwarg values
------------

Rather than passing in a dictionary of values, you can use kwargs instead if
you prefer:

.. code-block:: python

    >>> await Band.update(
    ...     name='Pythonistas 2'
    ... ).where(
    ...     Band.name == 'Pythonistas'
    ... )

-------------------------------------------------------------------------------

Query clauses
-------------

where
~~~~~

See :ref:`Where`.
