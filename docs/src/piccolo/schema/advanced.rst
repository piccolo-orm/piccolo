.. _AdvancedSchema:

Advanced
========

Postgres / CockroachDB Schemas
------------------------------

Postgres and CoackroachDB have a concept called **schemas**.

It's a way of grouping the tables in a database. To learn more:

* `Postgres docs <https://www.postgresql.org/docs/current/ddl-schemas.html>`_
* `CockroachDB docs <https://www.cockroachlabs.com/docs/stable/schema-design-overview.html>`_

To specify a table's schema, do the following:

.. code-block:: python

    class Band(Table, schema="music"):
        ...

    # The table will be created in the `music` schema:
    >>> await Band.create_table()

If the ``schema`` argument isn't specified, then the table is created in the
``public`` schema.

Migration support
~~~~~~~~~~~~~~~~~

Schemas are also fully supported in :ref:`database migrations <AutoMigrations>`.
For example, if we change the ``schema`` argument:

.. code-block:: python

    class Band(Table, schema="music_2"):
        ...

Then create an automatic migration and run it, then the table will be moved to
the new schema:

.. code-block:: bash

    >>> piccolo migrations new my_app --auto
    >>> piccolo migrations forwards my_app

-------------------------------------------------------------------------------

Readable
--------

Sometimes Piccolo needs a succinct representation of a row - for example, when
displaying a link in the :ref:`Piccolo Admin <PiccoloAdmin>`. Rather than
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

    await Band.select(Band.get_readable())

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
for example with :ref:`table_finder <TableFinder>`.

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

You can specify choices for a column, using Python's :class:`Enum <enum.Enum>` support.

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

    >>> await Shirt(size=Shirt.Size.large).save()

    >>> await Shirt.select()
    [{'id': 1, 'size': 'l'}]

Note how the value stored in the database is the ``Enum`` value (in this case ``'l'``).

You can also use the ``Enum`` in ``where`` clauses, and in most other situations
where a query requires a value.

.. code-block:: python

    >>> await Shirt.insert(
    ...     Shirt(size=Shirt.Size.small),
    ...     Shirt(size=Shirt.Size.medium)
    ... )

    >>> await Shirt.select().where(Shirt.size == Shirt.Size.small)
    [{'id': 1, 'size': 's'}]

Advantages
~~~~~~~~~~

By using choices, you get the following benefits:

* Signalling to other programmers what values are acceptable for the column.
* Improved storage efficiency (we can store ``'l'`` instead of ``'large'``).
* Piccolo Admin support

``Array`` columns
~~~~~~~~~~~~~~~~~

You can also use choices with :class:`Array <piccolo.columns.column_types.Array>`
columns.

.. code-block:: python

    class Ticket(Table):
        class Extras(str, enum.Enum):
            drink = "drink"
            snack = "snack"
            program = "program"

        extras = Array(Varchar(), choices=Extras)

Note how you pass ``choices`` to ``Array``, and not the ``base_column``:

.. code-block:: python

    # CORRECT:
    Array(Varchar(), choices=Extras)

    # INCORRECT:
    Array(Varchar(choices=Extras))

We can then use the ``Enum`` in our queries:

.. code-block:: python

    >>> await Ticket.insert(
    ...     Ticket(extras=[Extras.drink, Extras.snack]),
    ...     Ticket(extras=[Extras.program]),
    ... )


-------------------------------------------------------------------------------

Reflection
----------

This is a very advanced feature, which is only required for specialist use
cases. Currently, just Postgres is supported.

Instead of writing your ``Table`` definitions in a ``tables.py`` file, Piccolo
can dynamically create them at run time, by inspecting the database. These
``Table`` classes are then stored in memory, using a singleton object called
``TableStorage``.

Some example use cases:

* You have a very dynamic database, where new tables are being created
  constantly, so updating a ``tables.py`` is impractical.
* You use Piccolo on the command line to explore databases.

Full reflection
~~~~~~~~~~~~~~~

Here's an example, where we reflect the entire schema:

.. code-block:: python

    from piccolo.table_reflection import TableStorage

    storage = TableStorage()
    await storage.reflect(schema_name="music")

``Table`` objects are accessible from ``TableStorage.tables``:

.. code-block:: python

    >>> storage.tables
    {"music.Band": <class 'Band'>, ... }

    >>> Band = storage.tables["music.Band"]

Then you can use them like your normal ``Table`` classes:

.. code-block:: python

    >>> await Band.select()
    [{'id': 1, 'name': 'Pythonistas', 'manager': 1}, ...]


Partial reflection
~~~~~~~~~~~~~~~~~~

Full schema reflection can be a heavy process based on the size of your schema.
You can use ``include``, ``exclude`` and ``keep_existing`` parameters of
the ``reflect`` method to limit the overhead dramatically.

Only reflect the needed table(s):

.. code-block:: python

    from piccolo.table_reflection import TableStorage

    storage = TableStorage()
    await storage.reflect(schema_name="music", include=['band', ...])

Exclude table(s):

.. code-block:: python

    await storage.reflect(schema_name="music", exclude=['band', ...])

If you set ``keep_existing=True``, only new tables on the database will be
reflected and the existing tables in ``TableStorage`` will be left intact.

.. code-block:: python

    await storage.reflect(schema_name="music", keep_existing=True)

get_table
~~~~~~~~~

``TableStorage`` has a helper method named ``get_table``. If the table is
already present in the ``TableStorage``, this will return it and if the table
is not present, it will be reflected and returned.

.. code-block:: python

    Band = storage.get_table(tablename='band')

.. hint:: Reflection will automatically create ``Table`` classes for referenced
    tables too. For example, if ``Table1`` references ``Table2``, then
    ``Table2`` will automatically be added to ``TableStorage``.

-------------------------------------------------------------------------------

How to create custom column types
---------------------------------

Sometimes, the column types shipped with Piccolo don't meet your requirements, and you
will need to define your own column types.

Generally there are two ways to define your own column types:

* Create a subclass of an existing column type; or
* Directly subclass the :ref:`Column <ColumnTypes>` class.

Try to use the first method whenever possible because it is more straightforward and
can often save you some work. Otherwise, subclass :ref:`Column <ColumnTypes>`.

**Example**

In this example, we create a column type called ``MyColumn``, which is fundamentally
an ``Integer`` type but has a custom attribute ``custom_attr``:

.. code-block:: python

    from piccolo.columns import Integer

    class MyColumn(Integer):
        def __init__(self, *args, custom_attr: str = '', **kwargs):
            self.custom_attr = custom_attr
            super().__init__(*args, **kwargs)

        @property
        def column_type(self):
            return 'INTEGER'

.. hint:: It is **important** to specify the ``column_type`` property, which
    tells the database engine the **actual** storage type of the custom
    column.

Now we can use ``MyColumn`` in our table:

.. code-block:: python

    from piccolo.table import Table

    class MyTable(Table):
        my_col = MyColumn(custom_attr='foo')
        ...

And later we can retrieve the value of the attribute:

.. code-block:: python

    >>> MyTable.my_col.custom_attr
    'foo'