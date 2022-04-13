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

Piccolo won't let you run an update query without a :ref:`where clause <where>`,
unless you explicitly tell it to do so. This is to prevent accidentally
overwriting the data in a table.

.. code-block:: python

    >>> await Band.update()
    Raises: UpdateError

    # Works fine:
    >>> await Band.update({Band.popularity: 0}, force=True)

    # Or just add a where clause:
    >>> await Band.update({Band.popularity: 0}).where(Band.popularity < 50)

-------------------------------------------------------------------------------

Modifying values
----------------

As well as replacing values with new ones, you can also modify existing values,
for instance by adding an integer.

You can currently only combine two values together at a time.

Integer columns
~~~~~~~~~~~~~~~

You can add / subtract / multiply / divide values:

.. code-block:: python

    # Add 100 to the popularity of each band:
    await Band.update(
        {
            Band.popularity: Band.popularity + 100
        },
        force=True
    )

    # Decrease the popularity of each band by 100.
    await Band.update(
        {
            Band.popularity: Band.popularity - 100
        },
        force=True
    )

    # Multiply the popularity of each band by 10.
    await Band.update(
        {
            Band.popularity: Band.popularity * 10
        },
        force=True
    )

    # Divide the popularity of each band by 10.
    await Band.update(
        {
            Band.popularity: Band.popularity / 10
        },
        force=True
    )

    # You can also use the operators in reverse:
    await Band.update(
        {
            Band.popularity: 2000 - Band.popularity
        },
        force=True
    )

Varchar / Text columns
~~~~~~~~~~~~~~~~~~~~~~

You can concatenate values:

.. code-block:: python

    # Append "!!!" to each band name.
    await Band.update(
        {
            Band.name: Band.name + "!!!"
        },
        force=True
    )

    # Concatenate the values in each column:
    await Band.update(
        {
            Band.name: Band.name + Band.name
        },
        force=True
    )

    # Prepend "!!!" to each band name.
    await Band.update(
        {
            Band.popularity: "!!!" + Band.popularity
        },
        force=True
    )

Date / Timestamp / Timestamptz / Interval columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can add or substract a :class:`timedelta <datetime.timedelta>` to any of
these columns.

For example, if we have a ``Concert`` table, and we want each concert to start
one day later, we can simply do this:

.. code-block:: python

    await Concert.update(
        {
            Concert.starts: Concert.starts + datetime.timedelta(days=1)
        },
        force=True
    )

Likewise, we can decrease the values by 1 day:

.. code-block:: python

    await Concert.update(
        {
            Concert.starts: Concert.starts - datetime.timedelta(days=1)
        },
        force=True
    )

-------------------------------------------------------------------------------

Kwarg values
------------

Rather than passing in a dictionary of values, you can use kwargs instead if
you prefer:

.. code-block:: python

    await Band.update(
        name='Pythonistas 2'
    ).where(
        Band.name == 'Pythonistas'
    )

-------------------------------------------------------------------------------

Query clauses
-------------

where
~~~~~

See :ref:`Where`.
