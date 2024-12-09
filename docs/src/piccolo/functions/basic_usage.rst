Basic Usage
===========

Select queries
--------------

Functions can be used in ``select`` queries - here's an example, where we
convert the values to uppercase:

.. code-block:: python

    >>> from piccolo.query.functions import Upper

    >>> await Band.select(
    ...     Upper(Band.name, alias="name")
    ... )

    [{"name": "PYTHONISTAS"}]

Where clauses
-------------

Functions can also be used in ``where`` clauses.

.. code-block:: python

    >>> from piccolo.query.functions import Length

    >>> await Band.select(
    ...     Band.name
    ... ).where(
    ...     Length(Band.name) > 10
    ... )

    [{"name": "Pythonistas"}]

Update queries
--------------

And even in ``update`` queries:

.. code-block:: python

    >>> from piccolo.query.functions import Upper

    >>> await Band.update(
    ...     {Band.name: Upper(Band.name)},
    ...     force=True
    ... ).returning(Band.name)

    [{"name": "PYTHONISTAS"}, {"name": "RUSTACEANS"}, {"name": "C-SHARPS"}]

Pretty much everywhere.
