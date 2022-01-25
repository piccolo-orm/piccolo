Changes
=======

0.66.1
------

In Piccolo you can print out any query to see the SQL which will be generated:

.. code-block:: python

  >>> print(Band.select())
  SELECT "band"."id", "band"."name", "band"."manager", "band"."popularity" FROM band

It didn't represent ``UUID`` and ``datetime`` values correctly, which is now fixed (courtesy @theelderbeever).
See `PR 405 <https://github.com/piccolo-orm/piccolo/pull/405>`_.

-------------------------------------------------------------------------------

0.66.0
------

Using descriptors to improve MyPy support (`PR 399 <https://github.com/piccolo-orm/piccolo/pull/399>`_).

MyPy is now able to correctly infer the type in lots of different scenarios:

.. code-block:: python

  class Band(Table):
      name = Varchar()

  # MyPy knows this is a Varchar
  Band.name

  band = Band()
  band.name = "Pythonistas"  # MyPy knows we can assign strings when it's a class instance
  band.name  # MyPy knows we will get a string back

  band.name = 1  # MyPy knows this is an error, as we should only be allowed to assign strings

-------------------------------------------------------------------------------

0.65.1
------

Fixed bug with ``BaseUser`` and Piccolo API.

-------------------------------------------------------------------------------

0.65.0
------

The ``BaseUser`` table hashes passwords before storing them in the database.

When we create a fixture from the ``BaseUser`` table (using ``piccolo fixtures dump``),
it looks something like:

.. code-block:: json

  {
    "id": 11,
    "username": "bob",
    "password": "pbkdf2_sha256$10000$abc123",
  }

When we load the fixture (using ``piccolo fixtures load``) we need to be
careful in case ``BaseUser`` tries to hash the password again (it would then be a hash of
a hash, and hence incorrect). We now have additional checks in place to prevent
this.

Thanks to @mrbazzan for implementing this, and @sinisaos for help reviewing.

-------------------------------------------------------------------------------

0.64.0
------

Added initial support for ``ForeignKey`` columns referencing non-primary key
columns. For example:

.. code-block:: python

  class Manager(Table):
      name = Varchar()
      email = Varchar(unique=True)

  class Band(Table):
      manager = ForeignKey(Manager, target_column=Manager.email)

Thanks to @theelderbeever for suggesting this feature, and with help testing.

-------------------------------------------------------------------------------

0.63.1
------

Fixed an issue with the ``value_type`` of ``ForeignKey`` columns when
referencing a table with a custom primary key column (such as a ``UUID``).

-------------------------------------------------------------------------------

0.63.0
------

Added an ``exclude_imported`` option to ``table_finder``.

.. code-block:: python

  APP_CONFIG = AppConfig(
      table_classes=table_finder(['music.tables'], exclude_imported=True)
  )

It's useful when we want to import ``Table`` subclasses defined within a
module itself, but not imported ones:

.. code-block:: python

  # tables.py
  from piccolo.apps.user.tables import BaseUser # excluded
  from piccolo.columns.column_types import ForeignKey, Varchar
  from piccolo.table import Table


  class Musician(Table): # included
      name = Varchar()
      user = ForeignKey(BaseUser)

This was also possible using tags, but was less convenient. Thanks to @sinisaos
for reporting this issue.

-------------------------------------------------------------------------------

0.62.3
------

Fixed the error message in ``LazyTableReference``.

Fixed a bug with ``create_pydantic_model`` with nested models. For example:

.. code-block:: python

  create_pydantic_model(Band, nested=(Band.manager,))

Sometimes Pydantic couldn't uniquely identify the nested models. Thanks to
@wmshort and @sinisaos for their help with this.

-------------------------------------------------------------------------------

0.62.2
------

Added a max password length to the ``BaseUser`` table. By default it's set to
128 characters.

-------------------------------------------------------------------------------

0.62.1
------

Fixed a bug with ``Readable`` when it contains lots of joins.

``Readable`` is used to create a user friendly representation of a row in
Piccolo Admin.

-------------------------------------------------------------------------------

0.62.0
------

Added Many-To-Many support.

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
        bands = M2M(LazyTableReference("GenreToBand", module_path=__name__))


    # This is our joining table:
    class GenreToBand(Table):
        band = ForeignKey(Band)
        genre = ForeignKey(Genre)


    >>> await Band.select(Band.name, Band.genres(Genre.name, as_list=True))
    [
      {
        "name": "Pythonistas",
        "genres": ["Rock", "Folk"]
      },
      ...
    ]

See the docs for more details.

Many thanks to @sinisaos and @yezz123 for all the input.

-------------------------------------------------------------------------------

0.61.2
------

Fixed some edge cases where migrations would fail if a column name clashed with
a reserved Postgres keyword (for example ``order`` or ``select``).

We now have more robust tests for ``piccolo asgi new`` - as part of our CI we
actually run the generated ASGI app to make sure it works (thanks to @AliSayyah
and @yezz123 for their help with this).

We also improved docstrings across the project.

-------------------------------------------------------------------------------

0.61.1
------

Nicer ASGI template
~~~~~~~~~~~~~~~~~~~

When using ``piccolo asgi new`` to generate a web app, it now has a nicer home
page template, with improved styles.

Improved schema generation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Fixed a bug with ``piccolo schema generate`` where it would crash if the column
type was unrecognised, due to failing to parse the column's default value.
Thanks to @gmos for reporting this issue, and figuring out the fix.

Fix Pylance error
~~~~~~~~~~~~~~~~~

Added ``start_connection_pool`` and ``close_connection_pool`` methods to the
base ``Engine`` class (courtesy @gmos).

-------------------------------------------------------------------------------

0.61.0
------

The ``save`` method now supports a ``columns`` argument, so when updating a
row you can specify which values to sync back. For example:

.. code-block:: python

  band = await Band.objects().get(Band.name == "Pythonistas")
  band.name = "Super Pythonistas"
  await band.save([Band.name])

  # Alternatively, strings are also supported:
  await band.save(['name'])

Thanks to @trondhindenes for suggesting this feature.

-------------------------------------------------------------------------------

0.60.2
------

Fixed a bug with ``asyncio.gather`` not working with some query types. It was
due to them being dataclasses, and they couldn't be hashed properly. Thanks to
@brnosouza for reporting this issue.

-------------------------------------------------------------------------------

0.60.1
------

Modified the import path for ``MigrationManager`` in migration files. It was
confusing Pylance (VSCode's type checker). Thanks to @gmos for reporting and
investigating this issue.

-------------------------------------------------------------------------------

0.60.0
------

Secret columns
~~~~~~~~~~~~~~

All column types can now be secret, rather than being limited to the
``Secret`` column type which is a ``Varchar`` under the hood (courtesy
@sinisaos).

.. code-block:: python

  class Manager(Table):
      name = Varchar()
      net_worth = Integer(secret=True)

The reason this is useful is you can do queries such as:

.. code-block:: python

  >>> Manager.select(exclude_secrets=True).run_sync()
  [{'id': 1, 'name': 'Guido'}]

In the Piccolo API project we have ``PiccoloCRUD`` which is an incredibly
powerful way of building an API with very little code. ``PiccoloCRUD`` has an
``exclude_secrets`` option which lets you safely expose your data without
leaking sensitive information.

Pydantic improvements
~~~~~~~~~~~~~~~~~~~~~

max_recursion_depth
*******************

``create_pydantic_model`` now has a ``max_recursion_depth`` argument, which is
useful when using ``nested=True`` on large database schemas.

.. code-block:: python

  >>> create_pydantic_model(MyTable, nested=True, max_recursion_depth=3)

Nested tuple
************

You can now pass a tuple of columns as the argument to ``nested``:

.. code-block:: python

  >>> create_pydantic_model(Band, nested=(Band.manager,))

This gives you more control than just using ``nested=True``.

include_columns / exclude_columns
*********************************

You can now include / exclude columns from related tables. For example:

.. code-block:: python

  >>> create_pydantic_model(Band, nested=(Band.manager,), exclude_columns=(Band.manager.country))

Similarly:

.. code-block:: python

  >>> create_pydantic_model(Band, nested=(Band.manager,), include_columns=(Band.name, Band.manager.name))

-------------------------------------------------------------------------------

0.59.0
------

 * When using ``piccolo asgi new`` to generate a FastAPI app, the generated code
   is now cleaner. It also contains a ``conftest.py`` file, which encourages
   people to use ``piccolo tester run`` rather than using ``pytest`` directly.
 * Tidied up docs, and added logo.
 * Clarified the use of the ``PICCOLO_CONF`` environment variable in the docs
   (courtesy @theelderbeever).
 * ``create_pydantic_model`` now accepts an ``include_columns`` argument, in
   case you only want a few columns in your model, it's faster than using
   ``exclude_columns`` (courtesy @sinisaos).
 * Updated linters, and fixed new errors.

-------------------------------------------------------------------------------

0.58.0
------

Improved Pydantic docs
~~~~~~~~~~~~~~~~~~~~~~

The Pydantic docs used to be in the Piccolo API repo, but have been moved over
to this repo. We took this opportunity to improve them significantly with
additional examples. Courtesy @sinisaos.

Internal code refactoring
~~~~~~~~~~~~~~~~~~~~~~~~~

Some of the code has been optimised and cleaned up. Courtesy @yezz123.

Schema generation for recursive foreign keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``piccolo schema generate``, it would get stuck in a loop if a
table had a foreign key column which referenced itself. Thanks to @knguyen5
for reporting this issue, and @wmshort for implementing the fix. The output
will now look like:

.. code-block:: python

  class Employee(Table):
      name = Varchar()
      manager = ForeignKey("self")

Fixing a bug with Alter.add_column
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using the ``Alter.add_column`` API directly (not via migrations), it would
fail with foreign key columns. For example:

.. code-block:: python

  SomeTable.alter().add_column(
      name="my_fk_column",
      column=ForeignKey(SomeOtherTable)
    ).run_sync()

This has now been fixed. Thanks to @wmshort for discovering this issue.

create_pydantic_model improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additional fields can now be added to the Pydantic schema. This is useful
when using Pydantic's JSON schema functionality:

.. code-block:: python

    my_model = create_pydantic_model(Band, my_extra_field="Hello")
    >>> my_model.schema()
    {..., "my_extra_field": "Hello"}

This feature was added to support new features in Piccolo Admin.

Fixing a bug with import clashes in migrations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In certain situations it was possible to create a migration file with clashing
imports. For example:

.. code-block:: python

    from uuid import UUID
    from piccolo.columns.column_types import UUID

Piccolo now tries to detect these clashes, and prevent them. If they can't be
prevented automatically, a warning is shown to the user. Courtesy @0scarB.

-------------------------------------------------------------------------------

0.57.0
------

Added Python 3.10 support (courtesy @kennethcheo).

-------------------------------------------------------------------------------

0.56.0
------

Fixed schema generation bug
~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``piccolo schema generate`` to auto generate Piccolo ``Table``
classes from an existing database, it would fail in this situation:

 * A table has a column with an index.
 * The column name clashed with a Postgres type.

For example, we couldn't auto generate this ``Table`` class:

.. code-block:: python

  class MyTable(Table):
      time = Timestamp(index=True)

This is because ``time`` is a builtin Postgres type, and the ``CREATE INDEX``
statement being inspected in the database wrapped the column name in quotes,
which broke our regex.

Thanks to @knguyen5 for fixing this.

Improved testing docs
~~~~~~~~~~~~~~~~~~~~~

A convenience method called ``get_table_classes`` was added to ``Finder``.

``Finder`` is the main class in Piccolo for dynamically importing projects /
apps / tables / migrations etc.

``get_table_classes`` lets us easily get the ``Table`` classes for a project.
This makes writing unit tests easier, when we need to setup a schema.

.. code-block:: python

  from unittest import TestCase

  from piccolo.table import create_tables, drop_tables
  from piccolo.conf.apps import Finder

  TABLES = Finder().get_table_classes()

  class TestApp(TestCase):
      def setUp(self):
          create_tables(*TABLES)

      def tearDown(self):
          drop_tables(*TABLES)

      def test_app(self):
          # Do some testing ...
          pass

The docs were updated to reflect this.

When dropping tables in a unit test, remember to use ``piccolo tester run``, to
make sure the test database is used.

get_output_schema
~~~~~~~~~~~~~~~~~

``get_output_schema`` is the main entrypoint for database reflection in
Piccolo. It has been modified to accept an optional ``Engine`` argument, which
makes it more flexible.

-------------------------------------------------------------------------------

0.55.0
------

Table._meta.refresh_db
~~~~~~~~~~~~~~~~~~~~~~

Added the ability to refresh the database engine.

.. code-block:: python

  MyTable._meta.refresh_db()

This causes the ``Table`` to fetch the ``Engine`` again from your
``piccolo_conf.py`` file. The reason this is useful, is you might change the
``PICCOLO_CONF`` environment variable, and some ``Table`` classes have
already imported an engine. This is now used by the ``piccolo tester run``
command to ensure all ``Table`` classes have the correct engine.

ColumnMeta edge cases
~~~~~~~~~~~~~~~~~~~~~

Fixed an edge case where ``ColumnMeta`` couldn't be copied if it had extra
attributes added to it.

Improved column type conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When running migrations which change column types, Piccolo now provides the
``USING`` clause to the ``ALTER COLUMN`` DDL statement, which makes it more
likely that type conversion will be successful.

For example, if there is an ``Integer`` column, and it's converted to a
``Varchar`` column, the migration will run fine. In the past, running this in
reverse would fail. Now Postgres will try and cast the values back to integers,
which makes reversing migrations more likely to succeed.

Added drop_tables
~~~~~~~~~~~~~~~~~

There is now a convenience function for dropping several tables in one go. If
the database doesn't support ``CASCADE``, then the tables are sorted based on
their ``ForeignKey`` columns, so they're dropped in the correct order. It all
runs inside a transaction.

.. code-block:: python

  from piccolo.table import drop_tables

  drop_tables(Band, Manager)

This is a useful tool in unit tests.

Index support in schema generation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``piccolo schema generate``, Piccolo will now reflect the indexes
from the database into the generated ``Table`` classes. Thanks to @wmshort for
this.

-------------------------------------------------------------------------------

0.54.0
------
Added the ``db_column_name`` option to columns. This is for edge cases where
a legacy database is being used, with problematic column names. For example,
if a column is called ``class``, this clashes with a Python builtin, so the
following isn't possible:

.. code-block:: text

  class MyTable(Table):
      class = Varchar()  # Syntax error!

You can now do the following:

.. code-block:: python

  class MyTable(Table):
      class_ = Varchar(db_column_name='class')

Here are some example queries using it:

.. code-block:: python

  # Create - both work as expected
  MyTable(class_='Test').save().run_sync()
  MyTable.objects().create(class_='Test').run_sync()

  # Objects
  row = MyTable.objects().first().where(MyTable.class_ == 'Test').run_sync()
  >>> row.class_
  'Test'

  # Select
  >>> MyTable.select().first().where(MyTable.class_ == 'Test').run_sync()
  {'id': 1, 'class': 'Test'}

-------------------------------------------------------------------------------

0.53.0
------
An internal code clean up (courtesy @yezz123).

Dramatically improved CLI appearance when running migrations (courtesy
@wmshort).

Added a runtime reflection feature, where ``Table`` classes can be generated
on the fly from existing database tables (courtesy @AliSayyah). This is useful
when dealing with very dynamic databases, where tables are frequently being
added / modified, so hard coding them in a ``tables.py`` is impractical. Also,
for exploring databases on the command line. It currently just supports
Postgres.

Here's an example:

.. code-block:: python

  from piccolo.table_reflection import TableStorage

  storage = TableStorage()
  Band = await storage.get_table('band')
  >>> await Band.select().run()
  [{'id': 1, 'name': 'Pythonistas', 'manager': 1}, ...]

-------------------------------------------------------------------------------

0.52.0
------
Lots of improvements to ``piccolo schema generate``:

 * Dramatically improved performance, by executing more queries in parallel
   (courtesy @AliSayyah).
 * If a table in the database has a foreign key to a table in another
   schema, this will now work (courtesy @AliSayyah).
 * The column defaults are now extracted from the database (courtesy @wmshort).
 * The ``scale`` and ``precision`` values for ``Numeric`` / ``Decimal`` column
   types are extracted from the database (courtesy @wmshort).
 * The ``ON DELETE`` and ``ON UPDATE`` values for ``ForeignKey`` columns are
   now extracted from the database (courtesy @wmshort).

Added ``BigSerial`` column type (courtesy @aliereno).

Added GitHub issue templates (courtesy @AbhijithGanesh).

-------------------------------------------------------------------------------

0.51.1
------
Fixing a bug with ``on_delete`` and ``on_update`` not being set correctly.
Thanks to @wmshort for discovering this.

-------------------------------------------------------------------------------

0.51.0
------
Modified ``create_pydantic_model``, so ``JSON`` and ``JSONB`` columns have a
``format`` attribute of ``'json'``. This will be used by Piccolo Admin for
improved JSON support. Courtesy @sinisaos.

Fixing a bug where the ``piccolo fixtures load`` command wasn't registered
with the Piccolo CLI.

-------------------------------------------------------------------------------

0.50.0
------
The ``where`` clause can now accept multiple arguments (courtesy @AliSayyah):

.. code-block:: python

  Concert.select().where(
      Concert.venue.name == 'Royal Albert Hall',
      Concert.band_1.name == 'Pythonistas'
  ).run_sync()

It's another way of expressing `AND`. It's equivalent to both of these:

.. code-block:: python

  Concert.select().where(
      Concert.venue.name == 'Royal Albert Hall'
  ).where(
      Concert.band_1.name == 'Pythonistas'
  ).run_sync()

  Concert.select().where(
      (Concert.venue.name == 'Royal Albert Hall') & (Concert.band_1.name == 'Pythonistas')
  ).run_sync()

Added a ``create`` method, which is an easier way of creating objects (courtesy
@AliSayyah).

.. code-block:: python

    # This still works:
    band = Band(name="C-Sharps", popularity=100)
    band.save().run_sync()

    # But now we can do it in a single line using `create`:
    band = Band.objects().create(name="C-Sharps", popularity=100).run_sync()

Fixed a bug with ``piccolo schema generate`` where columns with unrecognised
column types were omitted from the output (courtesy @AliSayyah).

Added docs for the ``--trace`` argument, which can be used with Piccolo
commands to get a traceback if the command fails (courtesy @hipertracker).

Added ``DoublePrecision`` column type, which is similar to ``Real`` in that
it stores ``float`` values. However, those values are stored at greater
precision (courtesy @AliSayyah).

Improved ``AppRegistry``, so if a user only adds the app name (e.g. ``blog``),
instead of ``blog.piccolo_app``, it will now emit a warning, and will try to
import ``blog.piccolo_app`` (courtesy @aliereno).

-------------------------------------------------------------------------------

0.49.0
------
Fixed a bug with ``create_pydantic_model`` when used with a ``Decimal`` /
``Numeric`` column when no ``digits`` arguments was set (courtesy @AliSayyah).

Added the ``create_tables`` function, which accepts a sequence of ``Table``
subclasses, then sorts them based on their ``ForeignKey`` columns, and creates
them. This is really useful for people who aren't using migrations (for
example, when using Piccolo in a simple data science script). Courtesy
@AliSayyah.

.. code-block:: python

  from piccolo.tables import create_tables

  create_tables(Band, Manager, if_not_exists=True)

  # Equivalent to:
  Manager.create_table(if_not_exists=True).run_sync()
  Band.create_table(if_not_exists=True).run_sync()

Fixed typos with the new fixtures app - sometimes it was referred to as
``fixture`` and other times ``fixtures``. It's now standardised as
``fixtures`` (courtesy @hipertracker).

-------------------------------------------------------------------------------

0.48.0
------
The ``piccolo user create`` command can now be used by passing in command line
arguments, instead of using the interactive prompt (courtesy @AliSayyah).

For example ``piccolo user create --username=bob ...``.

This is useful when you want to create users in a script.

-------------------------------------------------------------------------------

0.47.0
------
You can now use ``pip install piccolo[all]``, which will install all optional
requirements.

-------------------------------------------------------------------------------

0.46.0
------
Added the fixtures app. This is used to dump data from a database to a JSON
file, and then reload it again. It's useful for seeding a database with
essential data, whether that's a colleague setting up their local environment,
or deploying to production.

To create a fixture:

.. code-block:: bash

  piccolo fixtures dump --apps=blog > fixture.json

To load a fixture:

.. code-block:: bash

  piccolo fixtures load fixture.json

As part of this change, Piccolo's Pydantic support was brought into this
library (prior to this it only existed within the ``piccolo_api`` library). At
a later date, the ``piccolo_api`` library will be updated, so it's Pydantic
code just proxies to what's within the main ``piccolo`` library.

-------------------------------------------------------------------------------

0.45.1
------
Improvements to ``piccolo schema generate``. It's now smarter about which
imports to include. Also, the ``Table`` classes output will now be sorted based
on their ``ForeignKey`` columns. Internally the sorting algorithm has been
changed to use the ``graphlib`` module, which was added in Python 3.9.

-------------------------------------------------------------------------------

0.45.0
------
Added the ``piccolo schema graph`` command for visualising your database
structure, which outputs a Graphviz file. It can then be turned into an
image, for example:

.. code-block:: bash

  piccolo schema map | dot -Tpdf -o graph.pdf

Also made some minor changes to the ASGI templates, to reduce MyPy errors.

-------------------------------------------------------------------------------

0.44.1
------
Updated ``to_dict`` so it works with nested objects, as introduced by the
``prefetch`` functionality.

For example:

.. code-block:: python

  band = Band.objects(Band.manager).first().run_sync()

  >>> band.to_dict()
  {'id': 1, 'name': 'Pythonistas', 'manager': {'id': 1, 'name': 'Guido'}}

It also works with filtering:

.. code-block:: python

  >>> band.to_dict(Band.name, Band.manager.name)
  {'name': 'Pythonistas', 'manager': {'name': 'Guido'}}

-------------------------------------------------------------------------------

0.44.0
------
Added the ability to prefetch related objects. Here's an example:

.. code-block:: python

  band = await Band.objects(Band.manager).run()
  >>> band.manager
  <Manager: 1>

If a table has a lot of ``ForeignKey`` columns, there's a useful shortcut,
which will return all of the related rows as objects.

.. code-block:: python

  concert = await Concert.objects(Concert.all_related()).run()
  >>> concert.band_1
  <Band: 1>
  >>> concert.band_2
  <Band: 2>
  >>> concert.venue
  <Venue: 1>

Thanks to @wmshort for all the input.

-------------------------------------------------------------------------------

0.43.0
------
Migrations containing ``Array``, ``JSON`` and ``JSONB`` columns should be
more reliable now. More unit tests were added to cover edge cases.

-------------------------------------------------------------------------------

0.42.0
------
You can now use ``all_columns`` at the root. For example:

.. code-block:: python

  await Band.select(
      Band.all_columns(),
      Band.manager.all_columns()
  ).run()

You can also exclude certain columns if you like:

.. code-block:: python

  await Band.select(
      Band.all_columns(exclude=[Band.id]),
      Band.manager.all_columns(exclude=[Band.manager.id])
  ).run()

-------------------------------------------------------------------------------

0.41.1
------
Fix a regression where if multiple tables are created in a single migration
file, it could potentially fail by applying them in the wrong order.

-------------------------------------------------------------------------------

0.41.0
------
Fixed a bug where if ``all_columns`` was used two or more levels deep, it would
fail. Thanks to @wmshort for reporting this issue.

Here's an example:

.. code-block:: python

  Concert.select(
      Concert.venue.name,
      *Concert.band_1.manager.all_columns()
  ).run_sync()

Also, the ``ColumnsDelegate`` has now been tweaked, so unpacking of
``all_columns`` is optional.

.. code-block:: python

  # This now works the same as the code above (we have omitted the *)
  Concert.select(
      Concert.venue.name,
      Concert.band_1.manager.all_columns()
  ).run_sync()

-------------------------------------------------------------------------------

0.40.1
------
Loosen the ``typing-extensions`` requirement, as it was causing issues when
installing ``asyncpg``.

-------------------------------------------------------------------------------

0.40.0
------
Added ``nested`` output option, which makes the response from a ``select``
query use nested dictionaries:

.. code-block:: python

  >>> await Band.select(Band.name, *Band.manager.all_columns()).output(nested=True).run()
  [{'name': 'Pythonistas', 'manager': {'id': 1, 'name': 'Guido'}}]

Thanks to @wmshort for the idea.

-------------------------------------------------------------------------------

0.39.0
------
Added ``to_dict`` method to ``Table``.

If you just use ``__dict__`` on a ``Table`` instance, you get some non-column
values. By using ``to_dict`` it's just the column values. Here's an example:

.. code-block:: python

  class MyTable(Table):
      name = Varchar()

  instance = MyTable.objects().first().run_sync()

  >>> instance.__dict__
  {'_exists_in_db': True, 'id': 1, 'name': 'foo'}

  >>> instance.to_dict()
  {'id': 1, 'name': 'foo'}

Thanks to @wmshort for the idea, and @aminalaee and @sinisaos for investigating
edge cases.

-------------------------------------------------------------------------------

0.38.2
------
Removed problematic type hint which assumed pytest was installed.

-------------------------------------------------------------------------------

0.38.1
------
Minor changes to ``get_or_create`` to make sure it handles joins correctly.

.. code-block:: python

  instance = (
      Band.objects()
      .get_or_create(
          (Band.name == "My new band")
          & (Band.manager.name == "Excellent manager")
      )
      .run_sync()
  )

In this situation, there are two columns called ``name`` - we need to make sure
the correct value is applied if the row doesn't exist.

-------------------------------------------------------------------------------

0.38.0
------
``get_or_create`` now supports more complex where clauses. For example:

.. code-block:: python

  row = await Band.objects().get_or_create(
      (Band.name == 'Pythonistas') & (Band.popularity == 1000)
  ).run()

And you can find out whether the row was created or not using
``row._was_created``.

Thanks to @wmshort for reporting this issue.

-------------------------------------------------------------------------------

0.37.0
------
Added ``ModelBuilder``, which can be used to generate data for tests (courtesy
@aminalaee).

-------------------------------------------------------------------------------

0.36.0
------
Fixed an issue where ``like`` and ``ilike`` clauses required a wildcard. For
example:

.. code-block:: python

  await Manager.select().where(Manager.name.ilike('Guido%')).run()

You can now omit wildcards if you like:

.. code-block:: python

  await Manager.select().where(Manager.name.ilike('Guido')).run()

Which would match on ``'guido'`` and ``'Guido'``, but not ``'Guidoxyz'``.

Thanks to @wmshort for reporting this issue.

-------------------------------------------------------------------------------

0.35.0
------
 * Improved ``PrimaryKey`` deprecation warning (courtesy @tonybaloney).
 * Added ``piccolo schema generate`` which creates a Piccolo schema from an
   existing database.
 * Added ``piccolo tester run`` which is a wrapper around pytest, and
   temporarily sets ``PICCOLO_CONF``, so a test database is used.
 * Added the ``get`` convenience method (courtesy @aminalaee). It returns the
   first matching record, or ``None`` if there's no match. For example:

  .. code-block:: python

      manager = await Manager.objects().get(Manager.name == 'Guido').run()

      # This is equivalent to:
      manager = await Manager.objects().where(Manager.name == 'Guido').first().run()

-------------------------------------------------------------------------------

0.34.0
------
Added the ``get_or_create`` convenience method (courtesy @aminalaee). Example
usage:

.. code-block:: python

    manager = await Manager.objects().get_or_create(
        Manager.name == 'Guido'
    ).run()

-------------------------------------------------------------------------------

0.33.1
------
 * Bug fix, where ``compare_dicts`` was failing in migrations if any ``Column``
   had an unhashable type as an argument. For example: ``Array(default=[])``.
   Thanks to @hipertracker for reporting this problem.
 * Increased the minimum version of orjson, so binaries are available for Macs
   running on Apple silicon (courtesy @hipertracker).

-------------------------------------------------------------------------------

0.33.0
------
Fix for auto migrations when using custom primary keys (thanks to @adriangb and
@aminalaee for investigating this issue).

-------------------------------------------------------------------------------

0.32.0
------
Migrations can now have a description, which is shown when using
``piccolo migrations check``. This makes migrations easier to identify (thanks
to @davidolrik for the idea).

-------------------------------------------------------------------------------

0.31.0
------
Added an ``all_columns`` method, to make it easier to retrieve all related
columns when doing a join. For example:

.. code-block:: python

    await Band.select(Band.name, *Band.manager.all_columns()).first().run()

Changed the instructions for installing additional dependencies, so they're
wrapped in quotes, to make sure it works on ZSH (i.e.
``pip install 'piccolo[postgres]'`` instead of
``pip install piccolo[postgres]``).

-------------------------------------------------------------------------------

0.30.0
------
The database drivers are now installed separately. For example:
``pip install piccolo[postgres]`` (courtesy @aminalaee).

For some users this might be a **breaking change** - please make sure that for
existing Piccolo projects, you have either ``asyncpg``, or
``piccolo[postgres]`` in your ``requirements.txt`` file.

-------------------------------------------------------------------------------

0.29.0
------
The user can now specify the primary key column (courtesy @aminalaee). For
example:

.. code-block:: python

    class RecordingStudio(Table):
        pk = UUID(primary_key=True)

The BlackSheep template generated by `piccolo asgi new` now supports mounting
of the Piccolo Admin (courtesy @sinisaos).

-------------------------------------------------------------------------------

0.28.0
------
Added aggregations functions, such as ``Sum``, ``Min``, ``Max`` and ``Avg``,
for use in select queries (courtesy @sinisaos).

-------------------------------------------------------------------------------

0.27.0
------
Added uvloop as an optional dependency, installed via `pip install piccolo[uvloop]`
(courtesy @aminalaee). uvloop is a faster implementation of the asyncio event
loop found in Python's standard library. When uvloop is installed, Piccolo will
use it to increase the performance of the Piccolo CLI, and web servers such as
Uvicorn will use it to increase the performance of your ASGI app.

-------------------------------------------------------------------------------

0.26.0
------
Added ``eq`` and ``ne`` methods to the ``Boolean`` column, which can be used
if linters complain about using ``SomeTable.some_column == True``.

-------------------------------------------------------------------------------

0.25.0
------
 * Changed the migration IDs, so the timestamp now includes microseconds. This
   is to make clashing migration IDs much less likely.
 * Added a lot of end-to-end tests for migrations, which revealed some bugs
   in ``Column`` defaults.

-------------------------------------------------------------------------------

0.24.1
------
A bug fix for migrations. See `issue 123 <https://github.com/piccolo-orm/piccolo/issues/123>`_
for more information.

-------------------------------------------------------------------------------

0.24.0
------
Lots of improvements to ``JSON`` and ``JSONB`` columns. Piccolo will now
automatically convert between Python types and JSON strings. For example, with
this schema:

.. code-block:: python

    class RecordingStudio(Table):
        name = Varchar()
        facilities = JSON()

We can now do the following:

.. code-block:: python

    RecordingStudio(
        name="Abbey Road",
        facilities={'mixing_desk': True}  # Will automatically be converted to a JSON string
    ).save().run_sync()

Similarly, when fetching data from a JSON column, Piccolo can now automatically
deserialise it.

.. code-block:: python

    >>> RecordingStudio.select().output(load_json=True).run_sync()
    [{'id': 1, 'name': 'Abbey Road', 'facilities': {'mixing_desk': True}]

    >>> studio = RecordingStudio.objects().first().output(load_json=True).run_sync()
    >>> studio.facilities
    {'mixing_desk': True}

-------------------------------------------------------------------------------

0.23.0
------
Added the ``create_table_class`` function, which can be used to create
``Table`` subclasses at runtime. This was required to fix an existing bug,
which was effecting migrations (see `issue 111 <https://github.com/piccolo-orm/piccolo/issues/111>`_
for more details).

-------------------------------------------------------------------------------

0.22.0
------
 * An error is now raised if a user tries to create a Piccolo app using
   ``piccolo app new`` with the same name as a builtin Python module, as it
   will cause strange bugs.
 * Fixing a strange bug where using an expression such as
   ``Concert.band_1.manager.id`` in a query would cause an error. It only
   happened if multiple joins were involved, and the last column in the chain
   was ``id``.
 * ``where`` clauses can now accept ``Table`` instances. For example:
   ``await Band.select().where(Band.manager == some_manager).run()``, instead
   of having to explicity reference the ``id``.

-------------------------------------------------------------------------------

0.21.2
------
Fixing a bug with serialising ``Enum`` instances in migrations. For example:
``Varchar(default=Colour.red)``.

-------------------------------------------------------------------------------

0.21.1
------
Fix missing imports in FastAPI and Starlette app templates.

-------------------------------------------------------------------------------

0.21.0
------
 * Added a ``freeze`` method to ``Query``.
 * Added BlackSheep as an option to ``piccolo asgi new``.

-------------------------------------------------------------------------------

0.20.0
------
Added ``choices`` option to ``Column``.

-------------------------------------------------------------------------------

0.19.1
------
 * Added ``piccolo user change_permissions`` command.
 * Added aliases for CLI commands.

-------------------------------------------------------------------------------

0.19.0
------
Changes to the ``BaseUser`` table - added a ``superuser``, and ``last_login``
column. These are required for upgrades to Piccolo Admin.

If you're using migrations, then running ``piccolo migrations forwards all``
should add these new columns for you.

If not using migrations, the ``BaseUser`` table can be upgraded using the
following DDL statements:

.. code-block:: sql

    ALTER TABLE piccolo_user ADD COLUMN "superuser" BOOLEAN NOT NULL DEFAULT false
    ALTER TABLE piccolo_user ADD COLUMN "last_login" TIMESTAMP DEFAULT null

-------------------------------------------------------------------------------

0.18.4
------
 * Fixed a bug when multiple tables inherit from the same mixin (thanks to
   @brnosouza).
 * Added a ``log_queries`` option to ``PostgresEngine``, which is useful during
   debugging.
 * Added the `inflection` library for converting ``Table`` class names to
   database table names. Previously, a class called ``TableA`` would wrongly
   have a table called ``table`` instead of ``table_a``.
 * Fixed a bug with ``SerialisedBuiltin.__hash__`` not returning a number,
   which could break migrations (thanks to @sinisaos).

-------------------------------------------------------------------------------

0.18.3
------
Improved ``Array`` column serialisation - needed to fix auto migrations.

-------------------------------------------------------------------------------

0.18.2
------
Added support for filtering ``Array`` columns.

-------------------------------------------------------------------------------

0.18.1
------
Add the ``Array`` column type as a top level import in ``piccolo.columns``.

-------------------------------------------------------------------------------

0.18.0
------
 * Refactored ``forwards`` and ``backwards`` commands for migrations, to make
   them easier to run programatically.
 * Added a simple ``Array`` column type.
 * ``table_finder`` now works if just a string is passed in, instead of having
   to pass in an array of strings.

-------------------------------------------------------------------------------

0.17.5
------
Catching database connection exceptions when starting the default ASGI app
created with ``piccolo asgi new`` - these errors exist if the Postgres
database hasn't been created yet.

-------------------------------------------------------------------------------

0.17.4
------
Added a ``help_text`` option to the ``Table`` metaclass. This is used in
Piccolo Admin to show tooltips.

-------------------------------------------------------------------------------

0.17.3
------
Added a ``help_text`` option to the ``Column`` constructor. This is used in
Piccolo Admin to show tooltips.

-------------------------------------------------------------------------------

0.17.2
------
 * Exposing ``index_type`` in the ``Column`` constructor.
 * Fixing a typo with ``start_connection_pool` and ``close_connection_pool`` -
   thanks to paolodina for finding this.
 * Fixing a typo in the ``PostgresEngine`` docs - courtesy of paolodina.

-------------------------------------------------------------------------------

0.17.1
------
Fixing a bug with ``SchemaSnapshot`` if column types were changed in migrations
- the snapshot didn't reflect the changes.

-------------------------------------------------------------------------------

0.17.0
------
 * Migrations now directly import ``Column`` classes - this allows users to
   create custom ``Column`` subclasses. Migrations previously only worked with
   the builtin column types.
 * Migrations now detect if the column type has changed, and will try and
   convert it automatically.

-------------------------------------------------------------------------------

0.16.5
------
The Postgres extensions that ``PostgresEngine`` tries to enable at startup
can now be configured.

-------------------------------------------------------------------------------

0.16.4
------
 * Fixed a bug with ``MyTable.column != None``
 * Added ``is_null`` and ``is_not_null`` methods, to avoid linting issues when
   comparing with None.

-------------------------------------------------------------------------------

0.16.3
------
 * Added ``WhereRaw``, so raw SQL can be used in where clauses.
 * ``piccolo shell run`` now uses syntax highlighting - courtesy of Fingel.

-------------------------------------------------------------------------------

0.16.2
------
Reordering the dependencies in requirements.txt when using ``piccolo asgi new``
as the latest FastAPI and Starlette versions are incompatible.

-------------------------------------------------------------------------------

0.16.1
------
Added ``Timestamptz`` column type, for storing datetimes which are timezone
aware.

-------------------------------------------------------------------------------

0.16.0
------
 * Fixed a bug with creating a ``ForeignKey`` column with ``references="self"``
   in auto migrations.
 * Changed migration file naming, so there are no characters in there which
   are unsupported on Windows.

-------------------------------------------------------------------------------

0.15.1
------
Changing the status code when creating a migration, and no changes were
detected. It now returns a status code of 0, so it doesn't fail build scripts.

-------------------------------------------------------------------------------

0.15.0
------
Added ``Bytea`` / ``Blob`` column type.

-------------------------------------------------------------------------------

0.14.13
-------
Fixing a bug with migrations which drop column defaults.

-------------------------------------------------------------------------------

0.14.12
-------
 * Fixing a bug where re-running ``Table.create(if_not_exists=True)`` would
   fail if it contained columns with indexes.
 * Raising a ``ValueError`` if a relative path is provided to ``ForeignKey``
   ``references``. For example, ``.tables.Manager``. The paths must be absolute
   for now.

-------------------------------------------------------------------------------

0.14.11
-------
Fixing a bug with ``Boolean`` column defaults, caused by the ``Table``
metaclass not being explicit enough when checking falsy values.

-------------------------------------------------------------------------------

0.14.10
-------
 * The ``ForeignKey`` ``references`` argument can now be specified using a
   string, or a ``LazyTableReference`` instance, rather than just a ``Table``
   subclass. This allows a ``Table`` to be specified which is in a Piccolo app,
   or Python module. The ``Table`` is only loaded after imports have completed,
   which prevents circular import issues.
 * Faster column copying, which is important when specifying joins, e.g.
   ``await Band.select(Band.manager.name).run()``.
 * Fixed a bug with migrations and foreign key contraints.

-------------------------------------------------------------------------------

0.14.9
------
Modified the exit codes for the ``forwards`` and ``backwards`` commands when no
migrations are left to run / reverse. Otherwise build scripts may fail.

-------------------------------------------------------------------------------

0.14.8
------
 * Improved the method signature of the ``output`` query clause (explicitly
   added args, instead of using ``**kwargs``).
 * Fixed a bug where ``output(as_list=True)`` would fail if no rows were found.
 * Made ``piccolo migrations forwards`` command output more legible.
 * Improved renamed table detection in migrations.
 * Added the ``piccolo migrations clean`` command for removing orphaned rows
   from the migrations table.
 * Fixed a bug where ``get_migration_managers`` wasn't inclusive.
 * Raising a ``ValueError`` if ``is_in`` or ``not_in`` query clauses are passed
   an empty list.
 * Changed the migration commands to be top level async.
 * Combined ``print`` and ``sys.exit`` statements.

-------------------------------------------------------------------------------

0.14.7
------
 * Added missing type annotation for ``run_sync``.
 * Updating type annotations for column default values - allowing callables.
 * Replaced instances of ``asyncio.run`` with ``run_sync``.
 * Tidied up aiosqlite imports.

-------------------------------------------------------------------------------

0.14.6
------
 * Added JSON and JSONB column types, and the arrow function for JSONB.
 * Fixed a bug with the distinct clause.
 * Added ``as_alias``, so select queries can override column names in the
   response (i.e. SELECT foo AS bar from baz).
 * Refactored JSON encoding into a separate utils file.

-------------------------------------------------------------------------------

0.14.5
------
 * Removed old iPython version recommendation in the ``piccolo shell run`` and
   ``piccolo playground run``, and enabled top level await.
 * Fixing outstanding mypy warnings.
 * Added optional requirements for the playground to setup.py

-------------------------------------------------------------------------------

0.14.4
------
 * Added ``piccolo sql_shell run`` command, which launches the psql or sqlite3
   shell, using the connection parameters defined in ``piccolo_conf.py``.
   This is convenient when you want to run raw SQL on your database.
 * ``run_sync`` now handles more edge cases, for example if there's already
   an event loop in the current thread.
 * Removed asgiref dependency.

-------------------------------------------------------------------------------

0.14.3
------
 * Queries can be directly awaited - ``await MyTable.select()``, as an
   alternative to using the run method ``await MyTable.select().run()``.
 * The ``piccolo asgi new`` command now accepts a ``name`` argument, which is
   used to populate the default database name within the template.

-------------------------------------------------------------------------------

0.14.2
------
 * Centralised code for importing Piccolo apps and tables - laying the
   foundation for fixtures.
 * Made orjson an optional dependency, installable using
   ``pip install piccolo[orjson]``.
 * Improved version number parsing in Postgres.

-------------------------------------------------------------------------------

0.14.1
------
Fixing a bug with dropping tables in auto migrations.

-------------------------------------------------------------------------------

0.14.0
------
Added ``Interval`` column type.

-------------------------------------------------------------------------------

0.13.5
------
 * Added ``allowed_hosts`` to ``create_admin`` in ASGI template.
 * Fixing bug with default ``root`` argument in some piccolo commands.

-------------------------------------------------------------------------------

0.13.4
------
 * Fixed bug with ``SchemaSnapshot`` when dropping columns.
 * Added custom ``__repr__`` method to ``Table``.

-------------------------------------------------------------------------------

0.13.3
------
Added ``piccolo shell run`` command for running adhoc queries using Piccolo.

-------------------------------------------------------------------------------

0.13.2
------
 * Fixing bug with auto migrations when dropping columns.
 * Added a ``root`` argument to ``piccolo asgi new``, ``piccolo app new`` and
   ``piccolo project new`` commands, to override where the files are placed.

-------------------------------------------------------------------------------

0.13.1
------
Added support for ``group_by`` and ``Count`` for aggregate queries.

-------------------------------------------------------------------------------

0.13.0
------
Added `required` argument to ``Column``. This allows the user to indicate which
fields must be provided by the user. Other tools can use this value when
generating forms and serialisers.

-------------------------------------------------------------------------------

0.12.6
------
 * Fixing a typo in ``TimestampCustom`` arguments.
 * Fixing bug in ``TimestampCustom`` SQL representation.
 * Added more extensive deserialisation for migrations.

-------------------------------------------------------------------------------

0.12.5
------
 * Improved ``PostgresEngine`` docstring.
 * Resolving rename migrations before adding columns.
 * Fixed bug serialising ``TimestampCustom``.
 * Fixed bug with altering column defaults to be non-static values.
 * Removed ``response_handler`` from ``Alter`` query.

-------------------------------------------------------------------------------

0.12.4
------
Using orjson for JSON serialisation when using the ``output(as_json=True)``
clause. It supports more Python types than ujson.

-------------------------------------------------------------------------------

0.12.3
------
Improved ``piccolo user create`` command - defaults the username to the current
system user.

-------------------------------------------------------------------------------

0.12.2
------
Fixing bug when sorting ``extra_definitions`` in auto migrations.

-------------------------------------------------------------------------------

0.12.1
------
 * Fixed typos.
 * Bumped requirements.

-------------------------------------------------------------------------------

0.12.0
------
 * Added ``Date`` and ``Time`` columns.
 * Improved support for column default values.
 * Auto migrations can now serialise more Python types.
 * Added ``Table.indexes`` method for listing table indexes.
 * Auto migrations can handle adding / removing indexes.
 * Improved ASGI template for FastAPI.

-------------------------------------------------------------------------------

0.11.8
------
ASGI template fix.

-------------------------------------------------------------------------------

0.11.7
------
 * Improved ``UUID`` columns in SQLite - prepending 'uuid:' to the stored value
   to make the type more explicit for the engine.
 * Removed SQLite as an option for ``piccolo asgi new`` until auto migrations
   are supported.

-------------------------------------------------------------------------------

0.11.6
------
Added support for FastAPI to ``piccolo asgi new``.

-------------------------------------------------------------------------------

0.11.5
------
Fixed bug in ``BaseMigrationManager.get_migration_modules`` - wasn't
excluding non-Python files well enough.

-------------------------------------------------------------------------------

0.11.4
------
 * Stopped ``piccolo migrations new`` from creating a config.py file - was
   legacy.
 * Added a README file to the `piccolo_migrations` folder in the ASGI template.

-------------------------------------------------------------------------------

0.11.3
------
Fixed `__pycache__` bug when using ``piccolo asgi new``.

-------------------------------------------------------------------------------

0.11.2
------
 * Showing a warning if trying auto migrations with SQLite.
 * Added a command for creating a new ASGI app - ``piccolo asgi new``.
 * Added a meta app for printing out the Piccolo version -
   ``piccolo meta version``.
 * Added example queries to the playground.

-------------------------------------------------------------------------------

0.11.1
------
 * Added ``table_finder``, for use in ``AppConfig``.
 * Added support for concatenating strings using an update query.
 * Added more tables to the playground, with more column types.
 * Improved consistency between SQLite and Postgres with ``UUID`` columns,
   ``Integer`` columns, and ``exists`` queries.

-------------------------------------------------------------------------------

0.11.0
------
Added ``Numeric`` and ``Real`` column types.

-------------------------------------------------------------------------------

0.10.8
------
Fixing a bug where Postgres versions without a patch number couldn't be parsed.

-------------------------------------------------------------------------------

0.10.7
------
Improving release script.

-------------------------------------------------------------------------------

0.10.6
------
Sorting out packaging issue - old files were appearing in release.

-------------------------------------------------------------------------------

0.10.5
------
Auto migrations can now run backwards.

-------------------------------------------------------------------------------

0.10.4
------
Fixing some typos with ``Table`` imports. Showing a traceback when piccolo_conf
can't be found by ``engine_finder``.

-------------------------------------------------------------------------------

0.10.3
------
Adding missing jinja templates to setup.py.

-------------------------------------------------------------------------------

0.10.2
------
Fixing a bug when using ``piccolo project new`` in a new project.

-------------------------------------------------------------------------------

0.10.1
------
Fixing bug with enum default values.

-------------------------------------------------------------------------------

0.10.0
------
Using targ for the CLI. Refactored some core code into apps.

-------------------------------------------------------------------------------

0.9.3
-----
Suppressing exceptions when trying to find the Postgres version, to avoid
an ``ImportError`` when importing `piccolo_conf.py`.

-------------------------------------------------------------------------------

0.9.2
-----
``.first()`` bug fix.

-------------------------------------------------------------------------------

0.9.1
-----
Auto migration fixes, and ``.first()`` method now returns None if no match is
found.

-------------------------------------------------------------------------------

0.9.0
-----
Added support for auto migrations.

-------------------------------------------------------------------------------

0.8.3
-----
Can use operators in update queries, and fixing 'new' migration command.

-------------------------------------------------------------------------------

0.8.2
-----
Fixing release issue.

-------------------------------------------------------------------------------

0.8.1
-----
Improved transaction support - can now use a context manager. Added ``Secret``,
``BigInt`` and ``SmallInt`` column types. Foreign keys can now reference the
parent table.

-------------------------------------------------------------------------------

0.8.0
-----
Fixing bug when joining across several tables. Can pass values directly into
the ``Table.update`` method. Added ``if_not_exists`` option when creating a
table.

-------------------------------------------------------------------------------

0.7.7
-----
Column sequencing matches the definition order.

-------------------------------------------------------------------------------

0.7.6
-----
Supporting `ON DELETE` and `ON UPDATE` for foreign keys. Recording reverse
foreign key relationships.

-------------------------------------------------------------------------------

0.7.5
-----
Made ``response_handler`` async. Made it easier to rename columns.

-------------------------------------------------------------------------------

0.7.4
-----
Bug fixes and dependency updates.

-------------------------------------------------------------------------------

0.7.3
-----
Adding missing ``__int__.py`` file.

-------------------------------------------------------------------------------

0.7.2
-----
Changed migration import paths.

-------------------------------------------------------------------------------

0.7.1
-----
Added ``remove_db_file`` method to ``SQLiteEngine`` - makes testing easier.

-------------------------------------------------------------------------------

0.7.0
-----
Renamed ``create`` to ``create_table``, and can register commands via
`piccolo_conf`.

-------------------------------------------------------------------------------

0.6.1
-----
Adding missing ``__init__.py`` files.

-------------------------------------------------------------------------------

0.6.0
-----
Moved ``BaseUser``. Migration refactor.

-------------------------------------------------------------------------------

0.5.2
-----
Moved drop table under ``Alter`` - to help prevent accidental drops.

-------------------------------------------------------------------------------

0.5.1
-----
Added ``batch`` support.

-------------------------------------------------------------------------------

0.5.0
-----
Refactored the ``Table`` Metaclass - much simpler now. Scoped more of the
attributes on ``Column`` to avoid name clashes. Added ``engine_finder`` to make
database configuration easier.

-------------------------------------------------------------------------------

0.4.1
-----
SQLite is now returning datetime objects for timestamp fields.

-------------------------------------------------------------------------------

0.4.0
-----
Refactored to improve code completion, along with bug fixes.

-------------------------------------------------------------------------------

0.3.7
-----
Allowing ``Update`` queries in SQLite.

-------------------------------------------------------------------------------

0.3.6
-----
Falling back to `LIKE` instead of `ILIKE` for SQLite.

-------------------------------------------------------------------------------

0.3.5
-----
Renamed ``User`` to ``BaseUser``.

-------------------------------------------------------------------------------

0.3.4
-----
Added ``ilike``.

-------------------------------------------------------------------------------

0.3.3
-----
Added value types to columns.

-------------------------------------------------------------------------------

0.3.2
-----
Default values infer the engine type.

-------------------------------------------------------------------------------

0.3.1
-----
Update click version.

-------------------------------------------------------------------------------

0.3
---
Tweaked API to support more auto completion. Join support in where clause.
Basic SQLite support - mostly for playground.

-------------------------------------------------------------------------------

0.2
---
Using ``QueryString`` internally to represent queries, instead of raw strings,
to harden against SQL injection.

-------------------------------------------------------------------------------

0.1.2
-----
Allowing joins across multiple tables.

-------------------------------------------------------------------------------

0.1.1
-----
Added playground.
