.. currentmodule:: piccolo.columns.m2m

###
M2M
###

Sometimes in database design you need `many-to-many (M2M) <https://en.wikipedia.org/wiki/Many-to-many_(data_model)>`_
relationships.

For example, we might have our ``Band`` table, and want to describe which genres of music
each band belongs to (e.g. rock and electronic). As each band can have multiple genres, a ``ForeignKey``
on the ``Band`` table won't suffice. Our options are using an ``Array`` / ``JSON`` / ``JSONB``
column, or using an ``M2M`` relationship.

Postgres and SQLite don't natively support ``M2M`` relationships - we create
them using a joining table which has foreign keys to each of the related tables
(in our example, ``Genre`` and ``Band``).

Take this schema as an example:

.. code-block:: python

    from piccolo.columns.column_types import (
        ForeignKey,
        LazyTableReference,
        Varchar
    )
    from piccolo.columns.m2m import M2M


    class Band(Table):
        name = Varchar()
        genres = M2M(LazyTableReference("GenreToBand", module_path=__name__))


    class Genre(Table):
        name = Varchar()


    # This is our joining table:
    class GenreToBand(Table):
        band = ForeignKey(Band)
        genre = ForeignKey(Genre)


.. note::
    We use ``LazyTableReference`` because when Python evaluates ``Band``,
    the ``GenreToBand`` class doesn't exist yet.

By using ``M2M`` it unlocks some powerful and convenient features.

-------------------------------------------------------------------------------

Select queries
==============

If we want to select each band, along with a list of genres, we can do this:

.. code-block:: python

    >>> await Band.select(Band.name, Band.genres(Genre.name))
    [
        {"name": "Pythonistas", "genres": ["Rock", "Folk"]},
        {"name": "Rustaceans", "genres": ["Folk"]},
        {"name": "C-Sharps", "genres": ["Rock", "Classical"]},
    ]

You can request whichever column you like from the related table:

.. code-block:: python

    >>> await Band.select(Band.name, Band.genres(Genre.id))
    [
        {"name": "Pythonistas", "genres": [1, 2]},
        {"name": "Rustaceans", "genres": [2]},
        {"name": "C-Sharps", "genres": [1, 3]},
    ]

-------------------------------------------------------------------------------

Objects queries
===============

Piccolo makes it easy working with objects and ``M2M`` relationship.


add_m2m
-------

.. currentmodule:: piccolo.table

.. automethod:: Table.add_m2m


get_m2m
-------

.. automethod:: Table.get_m2m
