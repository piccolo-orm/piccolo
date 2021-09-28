.. _AdvancedSchema:

Advanced
========

Readable
--------

Sometimes Piccolo needs a succinct representation of a row - for example, when
displaying a link in the Piccolo Admin GUI (see :ref:`Ecosystem`). Rather than
just displaying the row ID, we can specify something more user friendly using
``Readable``.

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns import Varchar
    from piccolo.columns.readable import Readable


    class Band(Table, tablename="music_band"):
        name = Varchar(length=100)

        @classmethod
        def get_readable(cls):
            return Readable(template="%s", columns=[cls.name])


Specifying the ``get_readable`` classmethod isn't just beneficial for Piccolo
tooling - you can also use it your own queries.

.. code-block:: python

    Band.select(Band.get_readable()).run_sync()

Here is an example of a more complex ``Readable``.

.. code-block:: python

    class Band(Table, tablename="music_band"):
        name = Varchar(length=100)

        @classmethod
        def get_readable(cls):
            return Readable(template="Band %s - %s", columns=[cls.id, cls.name])

As you can see, the template can include multiple columns, and can contain your
own text.

-------------------------------------------------------------------------------

.. _TableTags:

Table Tags
----------

``Table`` subclasses can be given tags. The tags can be used for filtering,
for example with ``table_finder`` (see :ref:`TableFinder`).

.. code-block:: python

    class Band(Table, tags=["music"]):
        name = Varchar(length=100)

-------------------------------------------------------------------------------

Mixins
------

If you're frequently defining the same columns over and over again, you can
use mixins to reduce the amount of repetition.

.. code-block:: python

    from piccolo.columns import Varchar, Boolean
    from piccolo.table import Table


    class FavouriteMixin:
        favourite = Boolean(default=False)


    class Manager(FavouriteMixin, Table):
        name = Varchar()

-------------------------------------------------------------------------------

Choices
-------

You can specify choices for a column, using Python's ``Enum`` support.

.. code-block:: python

    from enum import Enum

    from piccolo.columns import Varchar
    from piccolo.table import Table


    class Shirt(Table):
        class Size(str, Enum):
            small = 's'
            medium = 'm'
            large = 'l'

        size = Varchar(length=1, choices=Size)

We can then use the ``Enum`` in our queries.

.. code-block:: python

    >>> Shirt(size=Shirt.Size.large).save().run_sync()

    >>> Shirt.select().run_sync()
    [{'id': 1, 'size': 'l'}]

Note how the value stored in the database is the ``Enum`` value (in this case ``'l'``).

You can also use the ``Enum`` in ``where`` clauses, and in most other situations
where a query requires a value.

.. code-block:: python

    >>> Shirt.insert(
    >>>     Shirt(size=Shirt.Size.small),
    >>>     Shirt(size=Shirt.Size.medium)
    >>> ).run_sync()

    >>> Shirt.select().where(Shirt.size == Shirt.Size.small).run_sync()
    [{'id': 1, 'size': 's'}]

Advantages
~~~~~~~~~~

By using choices, you get the following benefits:

 * Signalling to other programmers what values are acceptable for the column.
 * Improved storage efficiency (we can store ``'l'`` instead of ``'large'``).
 * Piccolo Admin support
 

-------------------------------------------------------------------------------

Reflection
-------

Instead of hardcoding your tables, you can directly create Table objects from your database on your memory.
Reflected tables will be stored in a Singleton object named `TableStorage` and can be accessed globally.
This will be useful in very dynamic databases where new tables are created constantly.

.. hint:: Reflection automatically will create objects for referenced tables too.
          for example, if `Table1` references `Table2`, and `Table2` is not selected or it's not present in the same schema, It's object will be created and                 stored in `TableStorage`. 

Full schema reflection:

.. code-block:: python 

    >>> from piccolo.table_reflection import TableStorage
    >>> storage = TableStorage()
    >>> await storage.reflect(schema_name="music")
    >>> storage.tables  # `Table` objects are accessible from `storage.tables`.
    {"music.Band": <class 'Band'>, ... }
    >>> Band = storage.tables["music.Band"]
    # Then, you can use them like your normal Table classes.
    >>> Band.select().run_sync()
    
    
.. hint:: `TableStorage` has a helper method named `get_table`. If the table is already present in the `TableStorage`, this will return it.
and if the table is not present, it will be reflected and returned.

.. code-block:: python

    >>> storage = TableStorage()
    >>> Band = storage.get_table(tablename='band')
    
    
Only reflect the needed table(s):

.. code-block:: python 

    >>> from piccolo.table_reflection import TableStorage
    >>> storage = TableStorage()
    >>> await storage.reflect(schema_name="music", include=['band', ...])
    
    
Exclude table(s):

.. code-block:: python 

    >>> from piccolo.table_reflection import TableStorage
    >>> storage = TableStorage()
    >>> await storage.reflect(schema_name="music", exclude=['band', ...])
    
    
    
.. warning::
        Full schema reflection can be a heavy proccess based on size of your schema. make sure to not reflect the whole schema everytime in runtime.
        You can use `include`, `exclude` and `keep_existing` parameters of the `reflect` method to limit the overhead dramatically. 
        
Keep existing:

I you set this parameter to `True`, only new tables on the database will be reflected and the existing tables in `TableStorage` will be left intact.

.. code-block:: python 

    >>> from piccolo.table_reflection import TableStorage
    >>> storage = TableStorage()
    >>> await storage.reflect(schema_name="music", keep_existing=True)
    
    

