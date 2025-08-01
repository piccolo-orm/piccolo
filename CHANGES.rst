Changes
=======

1.28.0
------

Playground improvements
~~~~~~~~~~~~~~~~~~~~~~~

* Added an ``Array`` column to the playground (``Album.awards``), for easier
  experimentation with array columns.
* CoachroachDB is now supported in the playground (thanks to @sinisaos for this).

  .. code-block:: bash

    piccolo playground run --engine=cockroach

Functions
~~~~~~~~~

Added lots of useful array functions (thanks to @sinisaos for this).

Here's an example, where we can easily fix a typo in an array using ``replace``:

.. code-block:: python

  >>> await Album.update({
  ...     Album.awards: Album.awards.replace('Grammy Award 2021', 'Grammy Award 2022')
  ... }, force=True)

The documentation for functions has also been improved (e.g. how to create a
custom function).

The ``Cast`` function is now more flexible.

``Array`` concantenation
~~~~~~~~~~~~~~~~~~~~~~~~

Values can be prepended:

.. code-block:: python

  >>> await Album.update({
  ...     Album.awards: ['Grammy Award 2020'] + Album.awards
  ... }, force=True)

And multiple arrays can be concatenated in one go:

.. code-block:: python

  >>> await Album.update({
  ...     Album.awards: ['Grammy Award 2020'] + Album.awards + ['Grammy Award 2025']
  ... }, force=True)

``is_in`` and ``not_in`` sub queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can now use sub queries within ``is_in`` and ``not_in``  Thanks to
@sinisaos for this.

.. code-block:: python

  >>> await Band.select().where(
  ...     Band.id.is_in(
  ...         Concert.select(Concert.band_1).where(
  ...             Concert.starts >= datetime.datetime(year=2025, month=1, day=1)
  ...         )
  ...     )
  ... )

Other improvements
~~~~~~~~~~~~~~~~~~

* Auto convert a default value of ``0`` to ``0.0`` in ``Float`` columns.
* Modernised the type hints throughout the codebase (e.g. using ``list``
  instead of ``typing.List``). Thanks to @sinisaos for this.
* Fixed a bug with auto migrations, where the ``Array`` base column class
  wasn't being imported.
* Improved M2M query performance by using sub selects (thanks to @sinisaos for
  this).

-------------------------------------------------------------------------------

1.27.1
------

Improved the type annotations in ``ColumnKwargs`` - made some optional. Thanks
to @stronk7 and @sinisaos for their help with this.

-------------------------------------------------------------------------------

1.27.0
------

Improved auto completion / typo detection for column arguments.

For example:

.. code-block:: python

  class Band(Table):
      name = Varchar(nul=True)  # linters will now warn that nul is a typo (should be null)

Thanks to @sinisaos for this.

-------------------------------------------------------------------------------

1.26.1
------

Updated the BlackSheep ASGI template - thanks to @sinisaos for this.

Fixed a bug with auto migrations when a ``ForeignKey`` specifies
``target_column`` - multiple primary key columns were added to the migration
file. Thanks to @waldner for reporting this issue.

Added a tutorial for moving tables between Piccolo apps - thanks to
@sarvesh4396 for this.

-------------------------------------------------------------------------------

1.26.0
------

Improved auto migrations - ``ON DELETE`` and ``ON UPDATE`` can be modified
on ``ForeignKey`` columns. Thanks to @sinisaos for this.

-------------------------------------------------------------------------------

1.25.0
------

Improvements to Piccolo app creation. When running the following:

.. code-block:: bash

  piccolo app new my_app

It now validates that the app name (``my_app`` in this case) is valid as a
Python package.

Also, there is now a ``--register`` flag, which automatically adds the new app
to the ``APP_REGISTRY`` in ``piccolo_conf.py``.

.. code-block:: python

  piccolo app new my_app --register

Other changes:

* ``table_finder`` can now use relative modules.
* Updated the Esmerald ASGI template (thanks to @sinisaos for this).
* When using the ``remove`` method to delete a row from the database
  (``await some_band.remove()``), ``some_band._exists_in_db`` is now set to
  ``False``. Thanks to @sinisaos for this fix.

-------------------------------------------------------------------------------

1.24.2
------

Fixed a bug with ``delete`` queries which had joins in the ``where`` clause.
For example:

.. code-block:: python

  >>> await Band.delete().where(Band.manager.name == 'Guido')

Thanks to @HakierGrzonzo for reporting the issue, and @sinisaos for the fix.

-------------------------------------------------------------------------------

1.24.1
------

Fixed a bug with default values in ``Timestamp`` and ``Timestamptz`` columns.
Thanks to @splch for this.

-------------------------------------------------------------------------------

1.24.0
------

* Fixed a bug with ``get_or_create`` when a table has a column with both
  ``null=False`` and ``default=None`` - thanks to @bymoye for reporting this
  issue.
* If a ``PostgresEngine`` uses the ``dsn`` argument for ``asyncpg``, this is
  now used by ``piccolo sql_shell run``. Thanks to @abhishek-compro for
  suggesting this.
* Fixed the type annotation for the ``length`` argument of ``Varchar`` - it
  is allowed to be ``None``. Thanks to @Compro-Prasad for this.

-------------------------------------------------------------------------------

1.23.0
------

* Added Quart, Sanic, and Falcon as supported ASGI frameworks (thanks to
  @sinisaos for this).
* Fixed a bug with very large integers in SQLite.
* Fixed type annotation for ``Timestamptz`` default values (thanks to @Skelmis
  for this).

-------------------------------------------------------------------------------

1.22.0
------

Python 3.13 is now officially supported.

``JSON`` / ``JSONB`` querying has been significantly improved. For example, if
we have this table:

.. code-block:: python

  class RecordingStudio(Table):
      facilities = JSONB()

And the ``facilities`` column contains the following JSON data:

.. code-block:: python

    {
        "technicians": [
            {"name": "Alice Jones"},
            {"name": "Bob Williams"},
        ]
    }

We can get the first technician name as follows:

.. code-block:: python

    >>> await RecordingStudio.select(
    ...     RecordingStudio.facilities["technicians"][0]["name"].as_alias("name")
    ... ).output(load_json=True)
    [{'name': 'Alice Jones'}, ...]

``TableStorage`` (used for dynamically creating Piccolo ``Table`` classes from
an existing database) was improved, to support a Dockerised version of Piccolo
Admin, which is coming soon.

-------------------------------------------------------------------------------

1.21.0
------

Postgres 17 is now officially supported.

Fixed a bug with joins, when a ``ForeignKey`` column had ``db_column_name``
specified. Thanks to @jessemcl-flwls for reporting this issue.

-------------------------------------------------------------------------------

1.20.0
------

``get_related`` now works multiple layers deep:

.. code-block:: python

    concert = await Concert.objects().first()
    manager = await concert.get_related(Concert.band_1._.manager)

-------------------------------------------------------------------------------

1.19.1
------

Fixed a bug with the ``get_m2m`` method, which would raise a ``ValueError``
when no objects were found. It now handles this gracefully and returns an empty
list instead. Thanks to @nVitius for this fix.

Improved the ASGI templates (including a fix for the latest Litestar version).
Thanks to @sinisaos for this.

-------------------------------------------------------------------------------

1.19.0
------

Added support for row locking (i.e. ``SELECT ... FOR UPDATE``).

For example, if we have this table:

.. code-block:: python

  class Concert(Table):
      name = Varchar()
      tickets_available = Integer()

And we want to make sure that ``tickets_available`` never goes below 0, we can
do the following:

.. code-block:: python

  async def book_tickets(ticket_count: int):
      async with Concert._meta.db.transaction():
          concert = await Concert.objects().where(
              Concert.name == "Awesome Concert"
          ).first().lock_rows()

          if concert.tickets_available >= ticket_count:
              await concert.update_self({
                  Concert.tickets_available: Concert.tickets_available - ticket_count
              })
          else:
              raise ValueError("Not enough tickets are available!")

This means that when multiple transactions are running at the same time, it
isn't possible to book more tickets than are available.

Thanks to @dkopitsa for adding this feature.

-------------------------------------------------------------------------------

1.18.0
------

``update_self``
~~~~~~~~~~~~~~~

Added the ``update_self`` method, which is an alternative to the ``save``
method. Here's an example where it's useful:

.. code-block:: python

  # If we have a band object:
  >>> band = await Band.objects().get(name="Pythonistas")
  >>> band.popularity
  1000

  # We can increment the popularity, based on the current value in the
  # database:
  >>> await band.update_self({
  ...     Band.popularity: Band.popularity + 1
  ... })

  # The new value is set on the object:
  >>> band.popularity
  1001

  # It's safer than using the `save` method, because the popularity value on
  # the object might be out of date with what's in the database:
  band.popularity += 1
  await band.save()

Thanks to @trondhindenes for suggesting this feature.

Batch raw queries
~~~~~~~~~~~~~~~~~

The ``batch`` method can now be used with ``raw`` queries. For example:

.. code-block:: python

  async with await MyTable.raw("SELECT * FROM my_table").batch() as batch:
      async for _batch in batch:
          print(_batch)

This is useful when you expect a raw query to return a lot of data.

Thanks to @devsarvesh92 for suggesting this feature.

-------------------------------------------------------------------------------

1.17.1
------

Fixed a bug with migrations, where altering a column type from ``Integer`` to
``Float`` could fail. Thanks to @kurtportelli for reporting this issue.

-------------------------------------------------------------------------------

1.17.0
------

Each migration is automatically wrapped in a transaction - this can now be
disabled using the ``wrap_in_transaction`` argument:

.. code-block:: python

  manager = MigrationManager(
      wrap_in_transaction=False,
      ...
  )

This is useful when writing a manual migration, and you want to manage all of
the transaction logic yourself (or want multiple transactions).

``granian`` is now a supported server in the ASGI templates. Thanks to
@sinisaos for this.

-------------------------------------------------------------------------------

1.16.0
------

Added custom async ``TestCase`` subclasses, to help with testing.

For example ``AsyncTransactionTest``, which wraps each test in a transaction
automatically:

.. code-block:: python

  class TestBandEndpoint(AsyncTransactionTest):

      async def test_band_response(self):
          """
          Make sure the endpoint returns a 200.
          """
          # This data automatically gets removed from the database when the
          # test finishes:
          band = Band({Band.name: "Pythonistas"})
          await band.save()

          # Using an API testing client, like httpx:
          response = await client.get(f"/bands/{band.id}/")
          self.assertEqual(response.status_code, 200)

And ``AsyncTableTest``, which automatically creates and drops tables:

.. code-block:: python

  class TestBand(AsyncTableTest):

      # These tables automatically get created and dropped:
      tables = [Band]

      async def test_band(self):
          ...

-------------------------------------------------------------------------------

1.15.0
------

Improved ``refresh`` - it now works with prefetched objects. For example:

.. code-block:: python

  >>> band = await Band.objects(Band.manager).first()
  >>> band.manager.name
  "Guido"

  # If the manager has changed in the database, when we refresh the band, the
  # manager object will also be updated:
  >>> await band.refresh()
  >>> band.manager.name
  "New name"

Also, improved the error messages when creating a ``BaseUser`` - thanks to
@haaavk for this.

-------------------------------------------------------------------------------

1.14.0
------

Laying the foundations for alterative Postgres database drivers (e.g.
``psqlpy``). Thanks to @insani7y and @chandr-andr for their help with this.

.. warning::
  The SQL generated by Piccolo changed slightly in this release. Aliases used
  to be like ``"manager$name"`` but now they are like ``"manager.name"``
  (note ``$`` changed to ``.``). If you are using ``SelectRaw`` in your queries
  to refer to these columns, then they will need updating. Please let us know
  if you encounter any other issues.

-------------------------------------------------------------------------------

1.13.1
------

In Piccolo ``1.6.0`` we moved some aggregate functions to a new file. We now
re-export them from their original location to keep backwards compatibility.
Thanks to @sarvesh-deserve for reporting this issue.

-------------------------------------------------------------------------------

1.13.0
------

Improved ``LazyTableReference``, to help prevent circular import errors.

-------------------------------------------------------------------------------

1.12.0
------

* Added documentation for one to one fields.
* Upgraded ASGI templates (thanks to @sinisaos for this).
* Migrations can now be hardcoded as fake.
* Refactored tests to reduce boilerplate code.
* Updated documentation dependencies.

-------------------------------------------------------------------------------

1.11.0
------

Added datetime functions, for example ``Year``:

.. code-block:: python

    >>> from piccolo.query.functions import Year
    >>> await Concert.select(Year(Concert.starts, alias="starts_year"))
    [{'starts_year': 2024}]

Added the ``Concat`` function, for concatenating strings:

.. code-block:: python

    >>> from piccolo.query.functions import Concat
    >>> await Band.select(
    ...     Concat(
    ...         Band.name,
    ...         '-',
    ...         Band.manager._.name,
    ...         alias="name_and_manager"
    ...     )
    ... )
    [{"name_and_manager": "Pythonistas-Guido"}]

-------------------------------------------------------------------------------

1.10.0
------

Added ``not_any`` method for ``Array`` columns. This will return rows where an
array doesn't contain the given value. For example:

.. code-block:: python

  class MyTable(Table):
      array_column = Array(Integer())

  >>> await MyTable.select(
  ...     MyTable.array_column
  ... ).where(
  ...     MyTable.array_column.not_any(1)
  ... )
  [{"array_column": [4, 5, 6]}]

Also fixed a bunch of Pylance linter warnings across the codebase.

-------------------------------------------------------------------------------

1.9.0
-----

Added some math functions, for example ``Abs``, ``Ceil``, ``Floor`` and
``Round``.

.. code-block:: python

  >>> from piccolo.query.functions import Round
  >>> await Ticket.select(Round(Ticket.price, alias="price"))
  [{'price': 50.0}]

Added more operators to ``QueryString`` (multiply, divide, modulus, power), so
we can do things like:

.. code-block:: python

  >>> await Ticket.select(Round(Ticket.price) * 2)
  [{'price': 100.0}]

Fixed some edge cases around defaults for ``Array`` columns.

.. code-block:: python

  def get_default():
      # This used to fail:
      return [datetime.time(hour=8, minute=0)]

  class MyTable(Table):
      times = Array(Time(), default=get_default)

Fixed some deprecation warnings, and improved CockroachDB array tests.

-------------------------------------------------------------------------------

1.8.0
-----

Added the ``Cast`` function, for performing type conversion.

Here's an example, where we convert a ``timestamp`` to ``time``:

.. code-block:: python

    >>> from piccolo.columns import Time
    >>> from piccolo.query.functions import Cast

    >>> await Concert.select(Cast(Concert.starts, Time()))
    [{'starts': datetime.time(19, 0)}]

A new section was also added to the docs describing functions in more detail.

-------------------------------------------------------------------------------

1.7.0
-----

Arrays of ``Date`` / ``Time`` / ``Timestamp`` / ``Timestamptz`` now work in
SQLite.

For example:

.. code-block:: python

  class MyTable(Table):
      times = Array(Time())
      dates = Array(Date())
      timestamps = Array(Timestamp())
      timestamps_tz = Array(Timestamptz())

-------------------------------------------------------------------------------

1.6.0
-----

Added support for a bunch of Postgres functions, like ``Upper``, ``Lower``,
``Length``, and ``Ltrim``. They can be used in ``select`` queries:

.. code-block:: python

  from piccolo.query.functions.string import Upper
  >>> await Band.select(Upper(Band.name, alias="name"))
  [{"name": "PYTHONISTAS"}]

And also in ``where`` clauses:

.. code-block:: python

  >>> await Band.select().where(Upper(Band.manager.name) == 'GUIDO')
  [{"name": "Pythonistas"}]

-------------------------------------------------------------------------------

1.5.2
-----

Added an ``Album`` table to the playground, along with some other
improvements.

Fixed a bug with the ``output(load_json=True)`` clause, when used on joined
tables.

-------------------------------------------------------------------------------

1.5.1
-----

Fixed a bug with the CLI when reversing migrations (thanks to @metakot for
reporting this).

Updated the ASGI templates (thanks to @tarsil for adding Lilya).

-------------------------------------------------------------------------------

1.5.0
-----

Lots of internal improvements, mostly to support new functionality in Piccolo
Admin.

-------------------------------------------------------------------------------

1.4.2
-----

Improved how ``ModelBuilder`` handles recursive foreign keys.

-------------------------------------------------------------------------------

1.4.1
-----

Fixed an edge case with auto migrations.

If starting from a table like this, with a custom primary key column:

.. code-block:: python

  class MyTable(Table):
      id = UUID(primary_key=True)

When a foreign key is added to the table which references itself:

.. code-block:: python

  class MyTable(Table):
      id = UUID(primary_key=True)
      fk = ForeignKey("self")

The auto migrations could fail in some situations.

-------------------------------------------------------------------------------

1.4.0
-----

Improved how ``create_pydantic_model`` handles ``Array`` columns:

* Multidimensional arrays (e.g. ``Array(Array(Integer))``) have more accurate
  types.
* ``Array(Email())`` now validates that each item in the list is an email
  address.
* ``Array(Varchar(length=10))`` now validates that each item is the correct
  length (i.e. 10 in this example).

Other changes
~~~~~~~~~~~~~

Some Pylance errors were fixed in the codebase.

-------------------------------------------------------------------------------

1.3.2
-----

Fixed a bug with nested array columns containing ``BigInt``. For example:

.. code-block:: python

  class MyTable(Table):
      my_column = Array(Array(BigInt))

Thanks to @AmazingAkai for reporting this issue.

-------------------------------------------------------------------------------

1.3.1
-----

Fixed a bug with foreign keys which reference ``BigSerial`` primary keys.
Thanks to @Abdelhadi92 for reporting this issue.

-------------------------------------------------------------------------------

1.3.0
-----

Added the ``piccolo user list`` command - a quick and convenient way of listing
Piccolo Admin users from the command line.

``ModelBuilder`` now creates timezone aware ``datetime`` objects for
``Timestamptz`` columns.

Updated the ASGI templates.

SQLite auto migrations are now allowed. We used to raise an exception, but
now we output a warning instead. While SQLite auto migrations aren't as feature
rich as Postgres, they work fine for simple use cases.

-------------------------------------------------------------------------------

1.2.0
-----

There's now an alternative syntax for joins, which works really well with
static type checkers like Mypy and Pylance.

The traditional syntax (which continues to work as before):

.. code-block:: python

  # Get the band name, and the manager's name from a related table
  await Band.select(Band.name, Band.manager.name)

The alternative syntax is as follows:

.. code-block:: python

  await Band.select(Band.name, Band.manager._.name)

Note how we use ``._.`` instead of ``.`` after a ``ForeignKey``.

This offers a considerably better static typing experience. In the above
example, type checkers know that ``Band.manager._.name`` refers to the ``name``
column on the ``Manager`` table. This means typos can be detected, and code
navigation is easier.

Other changes
~~~~~~~~~~~~~

* Improve static typing for ``get_related``.
* Added support for the ``esmerald`` ASGI framework.

-------------------------------------------------------------------------------

1.1.1
-----

Piccolo allows the user to specify savepoint names which are used in
transactions. For example:

.. code-block:: python

    async with DB.transaction() as transaction:
        await Band.insert(Band(name='Pythonistas'))

        # Passing in a savepoint name is optional:
        savepoint_1 = await transaction.savepoint('savepoint_1')

        await Band.insert(Band(name='Terrible band'))

        # Oops, I made a mistake!
        await savepoint_1.rollback_to()

Postgres doesn't allow us to parameterise savepoint names, which means there's
a small chance of SQL injection, if for some reason the savepoint names were
generated from end-user input. Even though the likelihood is very low, it's
best to be safe. We now validate the savepoint name, to make sure it can only
contain certain safe characters. Thanks to @Skelmis for making this change.

-------------------------------------------------------------------------------

1.1.0
-----

Added support for Python 3.12.

Modified ``create_pydantic_model``, so additional information is returned in
the JSON schema to distinguish between ``Timestamp`` and ``Timestamptz``
columns. This will be used for future Piccolo Admin enhancements.

-------------------------------------------------------------------------------

1.0.0
-----

Piccolo v1 is now available!

We migrated to Pydantic v2, and also migrated Piccolo Admin to Vue 3, which
puts the project in a good place moving forward.

We don't anticipate any major issues for people who are upgrading. If you
encounter any bugs let us know.

Make sure you have v1 of Piccolo, Piccolo API, and Piccolo Admin.

-------------------------------------------------------------------------------

1.0a3
-----

Namespaced all custom values we added to Pydantic's JSON schema for easier
maintenance.

-------------------------------------------------------------------------------

1.0a2
-----

All of the changes from 0.120.0 merged into the v1 branch.

-------------------------------------------------------------------------------

0.121.0
-------

Modified the ``BaseUser.login`` logic so all code paths take the same time.
Thanks to @Skelmis for this.

-------------------------------------------------------------------------------

0.120.0
-------

Improved how ``ModelBuilder`` generates JSON data.

The number of password hash iterations used in ``BaseUser`` has been increased
to keep pace with the latest guidance from OWASP - thanks to @Skelmis for this.

Fixed a bug with auto migrations when the table is in a schema.

-------------------------------------------------------------------------------

1.0a1
-----

Initial alpha release of Piccolo v1, with Pydantic v2 support.

-------------------------------------------------------------------------------

0.119.0
-------

``ModelBuilder`` now works with ``LazyTableReference`` (which is used when we
have circular references caused by a ``ForeignKey``).

With this table:

.. code-block:: python

  class Band(Table):
      manager = ForeignKey(
          LazyTableReference(
              'Manager',
              module_path='some.other.folder.tables'
          )
      )

We can now create a dynamic test fixture:

.. code-block:: python

    my_model = await ModelBuilder.build(Band)

-------------------------------------------------------------------------------

0.118.0
-------

If you have lots of Piccolo apps, you can now create auto migrations for them
all in one go:

.. code-block:: bash

  piccolo migrations new all --auto

Thanks to @hoosnick for suggesting this new feature.

The documentation for running migrations has also been improved, as well as
improvements to the sorting of migrations based on their dependencies.

Support for Python 3.7 was dropped in this release as it's now end of life.

-------------------------------------------------------------------------------

0.117.0
-------

Version pinning Pydantic to v1, as v2 has breaking changes.

We will add support for Pydantic v2 in a future release.

Thanks to @sinisaos for helping with this.

-------------------------------------------------------------------------------

0.116.0
-------

Fixture formatting
~~~~~~~~~~~~~~~~~~

When creating a fixture:

.. code-block:: bash

  piccolo fixtures dump

The JSON output is now nicely formatted, which is useful because we can pipe
it straight to a file, and commit it to Git without having to manually run a
formatter on it.

.. code-block:: bash

  piccolo fixtures dump > my_fixture.json

Thanks to @sinisaos for this.

Protected table names
~~~~~~~~~~~~~~~~~~~~~

We used to raise a ``ValueError`` if a table was called ``user``.

.. code-block:: python

  class User(Table):  # ValueError!
      ...

It's because ``user`` is already used by Postgres (e.g. try ``SELECT user`` or
``SELECT * FROM user``).

We now emit a warning instead for these reasons:

* Piccolo wraps table names in quotes to avoid clashes with reserved keywords.
* Sometimes you're stuck with a table name from a pre-existing schema, and
  can't easily rename it.

Re-export ``WhereRaw``
~~~~~~~~~~~~~~~~~~~~~~

If you want to write raw SQL in your where queries you use ``WhereRaw``:

.. code-block:: python

  >>> Band.select().where(WhereRaw('TRIM(name) = {}', 'Pythonistas'))

You can now import it from ``piccolo.query`` to be consistent with
``SelectRaw`` and ``OrderByRaw``.

.. code-block:: python

  from piccolo.query import WhereRaw

-------------------------------------------------------------------------------

0.115.0
-------

Fixture upserting
~~~~~~~~~~~~~~~~~

Fixtures can now be upserted. For example:

.. code-block:: bash

  piccolo fixtures load my_fixture.json --on_conflict='DO UPDATE'

The options are:

* ``DO NOTHING``, meaning any rows with a matching primary key will be left
  alone.
* ``DO UPDATE``, meaning any rows with a matching primary key will be updated.

This is really useful, as you can now edit fixtures and load them multiple
times without getting foreign key constraint errors.

Schema fixes
~~~~~~~~~~~~

We recently added support for schemas, for example:

.. code-block:: python

  class Band(Table, schema='music'):
      ...

This release contains:

* A fix for migrations when changing a table's schema back to 'public' (thanks to
  @sinisaos for discovering this).
* A fix for ``M2M`` queries, when the tables are in a schema other than
  'public' (thanks to @quinnalfaro for reporting this).

Added ``distinct`` method to ``count`` queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We recently added support for ``COUNT DISTINCT`` queries. The syntax is:

.. code-block:: python

  await Concert.count(distinct=[Concert.start_date])

The following alternative syntax now also works (just to be consistent with
other queries like ``select``):

.. code-block:: python

  await Concert.count().distinct([Concert.start_date])

-------------------------------------------------------------------------------

0.114.0
-------

``count`` queries can now return the number of distinct rows. For example, if
we have this table:

.. code-block:: python

    class Concert(Table):
        band = Varchar()
        start_date = Date()

With this data:

.. table::
    :widths: auto

    ===========  ==========
    band         start_date
    ===========  ==========
    Pythonistas  2023-01-01
    Pythonistas  2023-02-03
    Rustaceans   2023-01-01
    ===========  ==========

We can easily get the number of unique concert dates:

.. code-block:: python

    >>> await Concert.count(distinct=[Concert.start_date])
    2

We could have just done this instead:

.. code-block:: python

    len(await Concert.select(Concert.start_date).distinct())

But it's far less efficient when you have lots of rows, because all of the
distinct rows need to be returned from the database.

Also, the docs for the ``count`` query, aggregate functions, and
``group_by`` clause were significantly improved.

Many thanks to @lqmanh and @sinisaos for their help with this.

-------------------------------------------------------------------------------

0.113.0
-------

If Piccolo detects a renamed table in an auto migration, it asks the user for
confirmation. When lots of tables have been renamed, Piccolo is now more
intelligent about when to ask for confirmation. Thanks to @sumitsharansatsangi
for suggesting this change, and @sinisaos for reviewing.

Also, fixed the type annotations for ``MigrationManager.add_table``.

-------------------------------------------------------------------------------

0.112.1
-------

Fixed a bug with serialising table classes in migrations.

-------------------------------------------------------------------------------

0.112.0
-------

Added support for schemas in Postgres and CockroachDB.

For example:

.. code-block:: python

  class Band(Table, schema="music"):
      ...

When creating the table, the schema will be created automatically if it doesn't
already exist.

.. code-block:: python

  await Band.create_table()

It also works with migrations. If we change the ``schema`` value for the table,
Piccolo will detect this, and create a migration for moving it to the new schema.

.. code-block:: python

  class Band(Table, schema="music_2"):
      ...

  # Piccolo will detect that the table needs to be moved to a new schema.
  >>> piccolo migrations new my_app --auto

-------------------------------------------------------------------------------

0.111.1
-------

Fixing a bug with ``ModelBuilder`` and ``Decimal`` / ``Numeric`` columns.

-------------------------------------------------------------------------------

0.111.0
-------

Added the ``on_conflict`` clause for ``insert`` queries. This enables **upserts**.

For example, here we insert some bands, and if they already exist then do
nothing:

.. code-block:: python

  await Band.insert(
      Band(name='Pythonistas'),
      Band(name='Rustaceans'),
      Band(name='C-Sharps'),
  ).on_conflict(action='DO NOTHING')

Here we insert some albums, and if they already exist then we update the price:

.. code-block:: python

  await Album.insert(
      Album(title='OK Computer', price=10.49),
      Album(title='Kid A', price=9.99),
      Album(title='The Bends', price=9.49),
  ).on_conflict(
      action='DO UPDATE',
      target=Album.title,
      values=[Album.price]
  )

Thanks to @sinisaos for helping with this.

-------------------------------------------------------------------------------

0.110.0
-------

ASGI frameworks
~~~~~~~~~~~~~~~

The ASGI frameworks in ``piccolo asgi new`` have been updated. ``starlite`` has
been renamed to ``litestar``. Thanks to @sinisaos for this.

ModelBuilder
~~~~~~~~~~~~

Generic types are now used in ``ModelBuilder``.

.. code-block:: python

  # mypy knows this is a `Band` instance:
  band = await ModelBuilder.build(Band)

``DISTINCT ON``
~~~~~~~~~~~~~~~

Added support for ``DISTINCT ON`` queries. For example, here we fetch the most
recent album for each band:

.. code-block:: python

  >>> await Album.select().distinct(
  ...     on=[Album.band]
  ... ).order_by(
  ...     Album.band
  ... ).order_by(
  ...     Album.release_date,
  ...     ascending=False
  ... )

Thanks to @sinisaos and @williamflaherty for their help with this.

-------------------------------------------------------------------------------

0.109.0
-------

Joins are now possible without foreign keys using ``join_on``.

For example:

.. code-block:: python

    class Manager(Table):
        name = Varchar(unique=True)
        email = Varchar()

    class Band(Table):
        name = Varchar()
        manager_name = Varchar()

    >>> await Band.select(
    ...     Band.name,
    ...     Band.manager_name.join_on(Manager.name).email
    ... )

-------------------------------------------------------------------------------

0.108.0
-------

Added support for savepoints within transactions.

.. code-block:: python

  async with DB.transaction() as transaction:
      await Manager.objects().create(name="Great manager")
      savepoint = await transaction.savepoint()
      await Manager.objects().create(name="Great manager")
      await savepoint.rollback_to()
      # Only the first manager will be inserted.

The behaviour of nested context managers has also been changed slightly.

.. code-block:: python

  async with DB.transaction():
      async with DB.transaction():
          # This used to raise an exception

We no longer raise an exception if there are nested transaction context
managers, instead the inner ones do nothing.

If you want the existing behaviour:

.. code-block:: python

  async with DB.transaction():
      async with DB.transactiona(allow_nested=False):
          # TransactionError!

-------------------------------------------------------------------------------

0.107.0
-------

Added the ``log_responses`` option to the database engines. This makes the
engine print out the raw response from the database for each query, which
is useful during debugging.

.. code-block:: python

  # piccolo_conf.py

  DB = PostgresEngine(
    config={'database': 'my_database'},
    log_queries=True,
    log_responses=True
  )

We also updated the Starlite ASGI template - it now uses the new import paths
(thanks to @sinisaos for this).

-------------------------------------------------------------------------------

0.106.0
-------

Joins now work within ``update`` queries. For example:

.. code-block:: python

  await Band.update({
      Band.name: 'Amazing Band'
  }).where(
      Band.manager.name == 'Guido'
  )

Other changes:

* Improved the template used  by ``piccolo app new`` when creating a new
  Piccolo app (it now uses ``table_finder``).

-------------------------------------------------------------------------------

0.105.0
-------

Improved the performance of select queries with complex joins. Many thanks to
@powellnorma and @sinisaos for their help with this.

-------------------------------------------------------------------------------

0.104.0
-------

Major improvements to Piccolo's typing / auto completion support.

For example:

.. code-block:: python

  >>> bands = await Band.objects()  # List[Band]

  >>> band = await Band.objects().first()  # Optional[Band]

  >>> bands = await Band.select().output(as_json=True)  # str

-------------------------------------------------------------------------------

0.103.0
-------

``SelectRaw``
~~~~~~~~~~~~~

This allows you to access features in the database which aren't exposed
directly by Piccolo. For example, Postgres functions:

.. code-block:: python

    from piccolo.query import SelectRaw

    >>> await Band.select(
    ...     Band.name,
    ...     SelectRaw("log(popularity) AS log_popularity")
    ... )
    [{'name': 'Pythonistas', 'log_popularity': 3.0}]

Large fixtures
~~~~~~~~~~~~~~

Piccolo can now load large fixtures using ``piccolo fixtures load``. The
rows are inserted in batches, so the database adapter doesn't raise any errors.

-------------------------------------------------------------------------------

0.102.0
-------

Migration file names
~~~~~~~~~~~~~~~~~~~~

The naming convention for migrations has changed slightly. It used to be just
a timestamp - for example:

.. code-block:: text

  2021-09-06T13-58-23-024723.py

By convention Python files should start with a letter, and only contain
``a-z``, ``0-9`` and ``_``, so the new format is:

.. code-block:: text

  my_app_2021_09_06T13_58_23_024723.py

.. note:: You can name a migration file anything you want (it's the ``ID``
  value inside it which is important), so this change doesn't break anything.

Enhanced Pydantic configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We now expose all of Pydantic's configuration options to
``create_pydantic_model``:

.. code-block:: python

  class MyPydanticConfig(pydantic.BaseConfig):
      extra = 'forbid'

  model = create_pydantic_model(
      table=MyTable,
      pydantic_config_class=MyPydanticConfig
  )

Thanks to @waldner for this.

Other changes
~~~~~~~~~~~~~

* Fixed a bug with ``get_or_create`` and null columns (thanks to @powellnorma
  for reporting this issue).
* Updated the Starlite ASGI template, so it uses the latest syntax for mounting
  Piccolo Admin (thanks to @sinisaos for this, and the Starlite team).

-------------------------------------------------------------------------------

0.101.0
-------

``piccolo fixtures load`` is now more intelligent about how it loads data, to
avoid foreign key constraint errors.

-------------------------------------------------------------------------------

0.100.0
-------

``Array`` columns now support choices.

.. code-block:: python

    class Ticket(Table):
        class Extras(str, enum.Enum):
            drink = "drink"
            snack = "snack"
            program = "program"

        extras = Array(Varchar(), choices=Extras)

We can then use the ``Enum`` in our queries:

.. code-block:: python

    >>> await Ticket.insert(
    ...     Ticket(extras=[Extras.drink, Extras.snack]),
    ...     Ticket(extras=[Extras.program]),
    ... )

This will also be supported in Piccolo Admin in the next release.

-------------------------------------------------------------------------------

0.99.0
------

You can now use the ``returning`` clause with ``delete`` queries.

For example:

.. code-block:: python

    >>> await Band.delete().where(Band.popularity < 100).returning(Band.name)
    [{'name': 'Terrible Band'}, {'name': 'Awful Band'}]

This also means you can count the number of deleted rows:

.. code-block:: python

    >>> len(await Band.delete().where(Band.popularity < 100).returning(Band.id))
    2

Thanks to @waldner for adding this feature.

-------------------------------------------------------------------------------

0.98.0
------

SQLite ``TransactionType``
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can now specify the transaction type for SQLite.

This is useful when using SQLite in production, as it's possible to get
``database locked`` errors if you're running lots of transactions concurrently,
and don't use the correct transaction type.

In this example we use an ``IMMEDIATE`` transaction:

.. code-block:: python

  from piccolo.engine.sqlite import TransactionType

  async with Band._meta.db.transaction(
      transaction_type=TransactionType.immediate
  ):
      band = await Band.objects().get_or_create(Band.name == 'Pythonistas')
      ...

We've added a `new tutorial <https://piccolo-orm.readthedocs.io/en/latest/piccolo/tutorials/using_sqlite_and_asyncio_effectively.html>`_
which explains this in more detail, as well as other tips for using asyncio and
SQLite together effectively.

Thanks to @powellnorma and @sinisaos for their help with this.

Other changes
~~~~~~~~~~~~~

* Fixed a bug with camelCase column names (we recommend using snake_case, but
  sometimes it's unavoidable when using Piccolo with an existing schema).
  Thanks to @sinisaos for this.
* Fixed a typo in the docs with ``raw`` queries - thanks to @StitiFatah for
  this.

-------------------------------------------------------------------------------

0.97.0
------

Some big improvements to ``order_by`` clauses.

It's now possible to combine ascending and descending:

.. code-block:: python

  await Band.select(
      Band.name,
      Band.popularity
  ).order_by(
      Band.name
  ).order_by(
      Band.popularity,
      ascending=False
  )

You can also order by anything you want using ``OrderByRaw``:

.. code-block:: python

  from piccolo.query import OrderByRaw

  await Band.select(
      Band.name
  ).order_by(
      OrderByRaw('random()')
  )

-------------------------------------------------------------------------------

0.96.0
------

Added the ``auto_update`` argument to ``Column``. Its main use case is columns
like ``modified_on`` where we want the value to be updated automatically each
time the row is saved.

.. code-block:: python

  class Band(Table):
      name = Varchar()
      popularity = Integer()
      modified_on = Timestamp(
        null=True,
        default=None,
        auto_update=datetime.datetime.now
      )

    # The `modified_on` column will automatically be updated to the current
    # timestamp:
    >>> await Band.update({
    ...     Band.popularity: Band.popularity + 100
    ... }).where(
    ...     Band.name == 'Pythonistas'
    ... )

It works with ``MyTable.update`` and also when using the ``save`` method on
an existing row.

-------------------------------------------------------------------------------

0.95.0
------

Made improvements to the Piccolo playground.

* Syntax highlighting is now enabled.
* The example queries are now async (iPython supports top level await, so
  this works fine).
* You can optionally use your own iPython configuration
  ``piccolo playground run --ipython_profile`` (for example if you want a
  specific colour scheme, rather than the one we use by default).

Thanks to @haffi96 for this. See `PR 656 <https://github.com/piccolo-orm/piccolo/pull/656>`_.

-------------------------------------------------------------------------------

0.94.0
------

Fixed a bug with ``MyTable.objects().create()`` and columns which are not
nullable. Thanks to @metakot for reporting this issue.

We used to use ``logging.getLogger(__file__)``, but as @Drapersniper pointed
out, the Python docs recommend ``logging.getLogger(__name__)``, so it has been
changed.

-------------------------------------------------------------------------------

0.93.0
------

* Fixed a bug with nullable ``JSON`` / ``JSONB`` columns and
  ``create_pydantic_model`` - thanks to @eneacosta for this fix.
* Made the ``Time`` column type importable from ``piccolo.columns``.
* Python 3.11 is now supported.
* Postgres 9.6 is no longer officially supported, as it's end of life, but
  Piccolo should continue to work with it just fine for now.
* Improved docs for transactions, added docs for the ``as_of`` clause in
  CockroachDB (thanks to @gnat for this), and added docs for
  ``add_raw_backwards``.

-------------------------------------------------------------------------------

0.92.0
------

Added initial support for Cockroachdb (thanks to @gnat for this massive
contribution).

Fixed Pylance warnings (thanks to @MiguelGuthridge for this).

-------------------------------------------------------------------------------

0.91.0
------

Added support for Starlite. If you use ``piccolo asgi new`` you'll see it as
an option for a router.

Thanks to @sinisaos for adding this, and @peterschutt for helping debug ASGI
mounting.

-------------------------------------------------------------------------------

0.90.0
------

Fixed an edge case, where a migration could fail if:

* 5 or more tables were being created at once.
* They all contained foreign keys to each other, as shown below.

.. code-block:: python

  class TableA(Table):
      pass

  class TableB(Table):
      fk = ForeignKey(TableA)

  class TableC(Table):
      fk = ForeignKey(TableB)

  class TableD(Table):
      fk = ForeignKey(TableC)

  class TableE(Table):
      fk = ForeignKey(TableD)


Thanks to @sumitsharansatsangi for reporting this issue.

-------------------------------------------------------------------------------

0.89.0
------

Made it easier to access the ``Email`` columns on a table.

.. code-block:: python

  >>> MyTable._meta.email_columns
  [MyTable.email_column_1, MyTable.email_column_2]

This was added for Piccolo Admin.

-------------------------------------------------------------------------------

0.88.0
------

Fixed a bug with migrations - when using ``db_column_name`` it wasn't being
used in some alter statements. Thanks to @theelderbeever for reporting this
issue.

.. code-block:: python

  class Concert(Table):
      # We use `db_column_name` when the column name is problematic - e.g. if
      # it clashes with a Python keyword.
      in_ = Varchar(db_column_name='in')

-------------------------------------------------------------------------------

0.87.0
------

When using ``get_or_create`` with ``prefetch`` the behaviour was inconsistent -
it worked as expected when the row already existed, but prefetch wasn't working
if the row was being created. This now works as expected:

.. code-block:: python

  >>> band = Band.objects(Band.manager).get_or_create(
  ...     (Band.name == "New Band 2") & (Band.manager == 1)
  ... )

  >>> band.manager
  <Manager: 1>
  >>> band.manager.name
  "Mr Manager"

Thanks to @backwardspy for reporting this issue.

-------------------------------------------------------------------------------

0.86.0
------

Added the ``Email`` column type. It's basically identical to ``Varchar``,
except that when we use ``create_pydantic_model`` we add email validation
to the generated Pydantic model.

.. code-block:: python

  from piccolo.columns.column_types import Email
  from piccolo.table import Table
  from piccolo.utils.pydantic import create_pydantic_model


  class MyTable(Table):
      email = Email()


  model = create_pydantic_model(MyTable)

  model(email="not a valid email")
  # ValidationError!

Thanks to @sinisaos for implementing this feature.

-------------------------------------------------------------------------------

0.85.1
------

Fixed a bug with migrations - when run backwards, ``raw`` was being called
instead of ``raw_backwards``. Thanks to @translunar for the fix.

-------------------------------------------------------------------------------

0.85.0
------

You can now append items to an array in an update query:

.. code-block:: python

  await Ticket.update({
      Ticket.seat_numbers: Ticket.seat_numbers + [1000]
  }).where(Ticket.id == 1)

Currently Postgres only. Thanks to @sumitsharansatsangi for suggesting this
feature.

-------------------------------------------------------------------------------

0.84.0
------

You can now preview the DDL statements which will be run by Piccolo migrations.

.. code-block:: bash

  piccolo migrations forwards my_app --preview

Thanks to @AliSayyah for adding this feature.

-------------------------------------------------------------------------------

0.83.0
------

We added support for Postgres read-slaves a few releases ago, but the ``batch``
clause didn't support it until now. Thanks to @guruvignesh01 for reporting
this issue, and @sinisaos for help implementing it.

.. code-block:: python

    # Returns 100 rows at a time from read_replica_db
    async with await Manager.select().batch(
        batch_size=100,
        node="read_replica_db",
    ) as batch:
        async for _batch in batch:
            print(_batch)


-------------------------------------------------------------------------------

0.82.0
------

Traditionally, when instantiating a ``Table``, you passed in column values
using kwargs:

.. code-block:: python

  >>> await Manager(name='Guido').save()

You can now pass in a dictionary instead, which makes it easier for static
typing analysis tools like Mypy to detect typos.

.. code-block:: python

  >>> await Manager({Manager.name: 'Guido'}).save()

See `PR 565 <https://github.com/piccolo-orm/piccolo/pull/565>`_ for more info.

-------------------------------------------------------------------------------

0.81.0
------

Added the ``returning`` clause to ``insert`` and ``update`` queries.

This can be used to retrieve data from the inserted / modified rows.

Here's an example, where we update the unpopular bands, and retrieve their
names, in a single query:

.. code-block:: python

  >>> await Band.update({
  ...     Band.popularity: Band.popularity + 5
  ... }).where(
  ...     Band.popularity < 10
  ... ).returning(
  ...     Band.name
  ... )
  [{'name': 'Bad sound band'}, {'name': 'Tone deaf band'}]

See `PR 564 <https://github.com/piccolo-orm/piccolo/pull/564>`_ and
`PR 563 <https://github.com/piccolo-orm/piccolo/pull/563>`_ for more info.

-------------------------------------------------------------------------------

0.80.2
------

Fixed a bug with ``Combination.__str__``, which meant that when printing out a
query for debugging purposes it was wasn't showing correctly (courtesy
@destos).

-------------------------------------------------------------------------------

0.80.1
------

Fixed a bug with Piccolo Admin and ``_get_related_readable``, which is used
to show a human friendly identifier for a row, rather than just the ID.

Thanks to @ethagnawl and @sinisaos for their help with this.

-------------------------------------------------------------------------------

0.80.0
------

There was a bug when doing joins with a ``JSONB`` column with ``as_alias``.

.. code-block:: python

  class User(Table, tablename="my_user"):
      name = Varchar(length=120)
      config = JSONB(default={})


  class Subscriber(Table, tablename="subscriber"):
      name = Varchar(length=120)
      user = ForeignKey(references=User)


  async def main():
      # This was failing:
      await Subscriber.select(
          Subscriber.name,
          Subscriber.user.config.as_alias("config")
      )

Thanks to @Anton-Karpenko for reporting this issue.

Even though this is a bug fix, the minor version number has been bumped because
the fix resulted in some refactoring of Piccolo's internals, so is a fairly big
change.

-------------------------------------------------------------------------------

0.79.0
------

Added a custom ``__repr__`` method to ``Table``'s metaclass. It's needed to
improve the appearance of our Sphinx docs. See
`issue 549 <https://github.com/piccolo-orm/piccolo/issues/549>`_ for more
details.

-------------------------------------------------------------------------------

0.78.0
------

Added the ``callback`` clause to ``select`` and ``objects`` queries (courtesy
@backwardspy). For example:

.. code-block:: python

  >>> await Band.select().callback(my_callback)

The callback can be a normal function or async function, which is called when
the query is successful. The callback can be used to modify the query's output.

It allows for some interesting and powerful code. Here's a very simple example
where we modify the query's output:

.. code-block:: python

  >>> def get_uppercase_names() -> Select:
  ...     def make_uppercase(response):
  ...         return [{'name': i['name'].upper()} for i in response]
  ...
  ...    return Band.select(Band.name).callback(make_uppercase)

  >>> await get_uppercase_names().where(Band.manager.name == 'Guido')
  [{'name': 'PYTHONISTAS'}]

Here's another example, where we perform validation on the query's output:

.. code-block:: python

  >>> def get_concerts() -> Select:
  ...     def check_length(response):
  ...         if len(response) == 0:
  ...             raise ValueError('No concerts!')
  ...         return response
  ...
  ...     return Concert.select().callback(check_length)

  >>> await get_concerts().where(Concert.band_1.name == 'Terrible Band')
  ValueError: No concerts!

At the moment, callbacks are just triggered when a query is successful, but in
the future other callbacks will be added, to hook into more of Piccolo's
internals.

-------------------------------------------------------------------------------

0.77.0
------

Added the ``refresh`` method. If you have an object which has gotten stale, and
want to refresh it, so it has the latest data from the database, you can now do
this:

.. code-block:: python

    # If we have an instance:
    band = await Band.objects().first()

    # And it has gotten stale, we can refresh it:
    await band.refresh()

Thanks to @trondhindenes for suggesting this feature.

-------------------------------------------------------------------------------

0.76.1
------

Fixed a bug with ``atomic`` when run async with a connection pool.

For example:

.. code-block:: python

  atomic = Band._meta.db.atomic()
  atomic.add(query_1, query_1)
  # This was failing:
  await atomic.run()

Thanks to @Anton-Karpenko for reporting this issue.

-------------------------------------------------------------------------------

0.76.0
------

create_db_tables / drop_db_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Added ``create_db_tables`` and ``create_db_tables_sync`` to replace
``create_tables``. The problem was ``create_tables`` was sync only, and was
inconsistent with the rest of Piccolo's API, which is async first.
``create_tables`` will continue to work for now, but is deprecated, and will be
removed in version 1.0.

Likewise, ``drop_db_tables`` and ``drop_db_tables_sync`` have replaced
``drop_tables``.

When calling ``create_tables`` / ``drop_tables`` within other async libraries
(such as `ward <https://github.com/darrenburns/ward>`_) it was sometimes
unreliable - the best solution was just to make async versions of these
functions. Thanks to @backwardspy for reporting this issue.

``BaseUser`` password validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We centralised the password validation logic in ``BaseUser`` into a method
called ``_validate_password``. This is needed by Piccolo API, but also makes it
easier for users to override this logic if subclassing ``BaseUser``.

More ``run_sync`` refinements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``run_sync``, which is the main utility function which Piccolo uses to run
async code, has been further simplified for Python > v3.10 compatibility.

-------------------------------------------------------------------------------

0.75.0
------

Changed how ``piccolo.utils.sync.run_sync`` works, to prevent a warning on
Python 3.10. Thanks to @Drapersniper for reporting this issue.

Lots of documentation improvements - particularly around testing, and Docker
deployment.

-------------------------------------------------------------------------------

0.74.4
------

``piccolo schema generate`` now outputs a warning when it can't detect the
``ON DELETE`` and ``ON UPDATE`` for a ``ForeignKey``, rather than raising an
exception. Thanks to @theelderbeever for reporting this issue.

``run_sync`` doesn't use the connection pool by default anymore. It was causing
issues when an app contained sync and async code. Thanks to @WintonLi for
reporting this issue.

Added a tutorial to the docs for using Piccolo with an existing project and
database. Thanks to @virajkanwade for reporting this issue.

-------------------------------------------------------------------------------

0.74.3
------

If you had a table containing an array of ``BigInt``, then migrations could
fail:

.. code-block:: python

  from piccolo.table import Table
  from piccolo.columns.column_types import Array, BigInt

  class MyTable(Table):
      my_column = Array(base_column=BigInt())

It's because the ``BigInt`` base column needs access to the parent table to
know if it's targeting Postgres or SQLite. See `PR 501 <https://github.com/piccolo-orm/piccolo/pull/501>`_.

Thanks to @cheesycod for reporting this issue.

-------------------------------------------------------------------------------

0.74.2
------

If a user created a custom ``Column`` subclass, then migrations would fail.
For example:

.. code-block:: python

  class CustomColumn(Varchar):
      def __init__(self, custom_arg: str = '', *args, **kwargs):
          self.custom_arg = custom_arg
          super().__init__(*args, **kwargs)

      @property
      def column_type(self):
          return 'VARCHAR'

See `PR 497 <https://github.com/piccolo-orm/piccolo/pull/497>`_. Thanks to
@WintonLi for reporting this issue.

-------------------------------------------------------------------------------

0.74.1
------

When using ``pip install piccolo[all]`` on Windows it would fail because uvloop
isn't supported. Thanks to @jack1142 for reporting this issue.

-------------------------------------------------------------------------------

0.74.0
------

We've had the ability to bulk modify rows for a while. Here we append ``'!!!'``
to each band's name:

.. code-block:: python

  >>> await Band.update({Band.name: Band.name + '!!!'}, force=True)

It only worked for some columns - ``Varchar``, ``Text``, ``Integer`` etc.

We now allow ``Date``, ``Timestamp``, ``Timestamptz`` and ``Interval`` columns
to be bulk modified using a ``timedelta``. Here we modify each concert's start
date, so it's one day later:

.. code-block:: python

  >>> await Concert.update(
  ...     {Concert.starts: Concert.starts + timedelta(days=1)},
  ...     force=True
  ... )

Thanks to @theelderbeever for suggesting this feature.

-------------------------------------------------------------------------------

0.73.0
------

You can now specify extra nodes for a database. For example, if you have a
read replica.

.. code-block:: python

  DB = PostgresEngine(
      config={'database': 'main_db'},
      extra_nodes={
          'read_replica_1': PostgresEngine(
              config={
                  'database': 'main_db',
                  'host': 'read_replica_1.my_db.com'
              }
          )
      }
  )

And can then run queries on these other nodes:

.. code-block:: python

  >>> await MyTable.select().run(node="read_replica_1")

See `PR 481 <https://github.com/piccolo-orm/piccolo/pull/481>`_. Thanks to
@dashsatish for suggesting this feature.

Also, the ``targ`` library has been updated so it tells users about the
``--trace`` argument which can be used to get a full traceback when a CLI
command fails.

-------------------------------------------------------------------------------

0.72.0
------

Fixed typos with ``drop_constraints``. Courtesy @smythp.

Lots of documentation improvements, such as fixing Sphinx's autodoc for the
``Array`` column.

``AppConfig`` now accepts a ``pathlib.Path`` instance. For example:

.. code-block:: python

  # piccolo_app.py

  import pathlib

  APP_CONFIG = AppConfig(
      app_name="blog",
      migrations_folder_path=pathlib.Path(__file__) /  "piccolo_migrations"
  )

Thanks to @theelderbeever for recommending this feature.

-------------------------------------------------------------------------------

0.71.1
------

Fixed a bug with ``ModelBuilder`` and nullable columns (see `PR 462 <https://github.com/piccolo-orm/piccolo/pull/462>`_).
Thanks to @fiolet069 for reporting this issue.

-------------------------------------------------------------------------------

0.71.0
------

The ``ModelBuilder`` class, which is used to generate mock data in tests, now
supports ``Array`` columns. Courtesy @backwardspy.

Lots of internal code optimisations and clean up. Courtesy @yezz123.

Added docs for troubleshooting common MyPy errors.

Also thanks to @adriangb for helping us with our dependency issues.

-------------------------------------------------------------------------------

0.70.1
------

Fixed a bug with auto migrations. If renaming multiple columns at once, it
could get confused. Thanks to @theelderbeever for reporting this issue, and
@sinisaos for helping to replicate it. See `PR 457 <https://github.com/piccolo-orm/piccolo/pull/457>`_.

-------------------------------------------------------------------------------

0.70.0
------

We ran a profiler on the Piccolo codebase and identified some optimisations.
For example, we were calling ``self.querystring`` multiple times in a method,
rather than assigning it to a local variable.

We also ran a linter which identified when list / set / dict comprehensions
could be more efficient.

The performance is now slightly improved (especially when fetching large
numbers of rows from the database).

Example query times on a MacBook, when fetching 1000 rows from a local Postgres
database (using ``await SomeTable.select()``):

* 8 ms without a connection pool
* 2 ms with a connection pool

As you can see, having a connection pool is the main thing you can do to
improve performance.

Thanks to @AliSayyah for all his work on this.

-------------------------------------------------------------------------------

0.69.5
------

Made improvements to ``piccolo schema generate``, which automatically generates
Piccolo ``Table`` classes from an existing database.

There were situations where it would fail ungracefully when it couldn't parse
an index definition. It no longer crashes, and we print out the problematic
index definitions. See `PR 449 <https://github.com/piccolo-orm/piccolo/pull/449>`_.
Thanks to @gmos for originally reporting this issue.

We also improved the error messages if schema generation fails for some reason
by letting the user know which table caused the error. Courtesy @AliSayyah.

-------------------------------------------------------------------------------

0.69.4
------

We used to raise a ``ValueError`` if a column was both ``null=False`` and
``default=None``. This has now been removed, as there are situations where
it's valid for columns to be configured that way. Thanks to @gmos for
suggesting this change.

-------------------------------------------------------------------------------

0.69.3
------

The ``where`` clause now raises a ``ValueError`` if a boolean value is
passed in by accident. This was possible in the following situation:

.. code-block:: python

  await Band.select().where(Band.has_drummer is None)

Piccolo can't override the ``is`` operator because Python doesn't allow it,
so ``Band.has_drummer is None`` will always equal ``False``. Thanks to
@trondhindenes for reporting this issue.

We've also put a lot of effort into improving documentation throughout the
project.

-------------------------------------------------------------------------------

0.69.2
------

* Lots of documentation improvements, including how to customise ``BaseUser``
  (courtesy @sinisaos).
* Fixed a bug with creating indexes when the column name clashes with a SQL
  keyword (e.g. ``'order'``). See `Pr 433 <https://github.com/piccolo-orm/piccolo/pull/433>`_.
  Thanks to @wmshort for reporting this issue.
* Fixed an issue where some slots were incorrectly configured (courtesy
  @ariebovenberg). See `PR 426 <https://github.com/piccolo-orm/piccolo/pull/426>`_.

-------------------------------------------------------------------------------

0.69.1
------

Fixed a bug with auto migrations which rename columns - see
`PR 423 <https://github.com/piccolo-orm/piccolo/pull/423>`_. Thanks to
@theelderbeever for reporting this, and @sinisaos for help investigating.

-------------------------------------------------------------------------------

0.69.0
------

Added `Xpresso <https://xpresso-api.dev/>`_ as a supported ASGI framework when
using ``piccolo asgi new`` to generate a web app.

Thanks to @sinisaos for adding this template, and @adriangb for reviewing.

We also took this opportunity to update our FastAPI and BlackSheep ASGI
templates.

-------------------------------------------------------------------------------

0.68.0
------

``Update`` queries without a ``where`` clause
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you try and perform an update query without a ``where`` clause you will now
get an error:

.. code-block:: python

  >>> await Band.update({Band.name: 'New Band'})
  UpdateError

If you want to update all rows in the table, you can still do so, but you must
pass ``force=True``.

.. code-block:: python

  >>> await Band.update({Band.name: 'New Band'}, force=True)

This is a similar to ``delete`` queries, which require a ``where`` clause or
``force=True``.

It was pointed out by @theelderbeever that an accidental mass update is almost
as bad as a mass deletion, which is why this safety measure has been added.

See `PR 412 <https://github.com/piccolo-orm/piccolo/pull/412>`_.

.. warning:: This is a breaking change. It you're doing update queries without
  a where clause, you will need to add ``force=True``.

``JSONB`` improvements
~~~~~~~~~~~~~~~~~~~~~~

Fixed some bugs with nullable ``JSONB`` columns. A value of ``None`` is now
stored as ``null`` in the database, instead of the JSON string ``'null'``.
Thanks to @theelderbeever for reporting this.

See `PR 413 <https://github.com/piccolo-orm/piccolo/pull/413>`_.

-------------------------------------------------------------------------------

0.67.0
------

create_user
~~~~~~~~~~~

``BaseUser`` now has a ``create_user`` method, which adds some extra password
validation vs just instantiating and saving ``BaseUser`` directly.

.. code-block:: python

  >>> await BaseUser.create_user(username='bob', password='abc123XYZ')
  <BaseUser: 1>

We check that passwords are a reasonable length, and aren't already hashed.
See `PR 402 <https://github.com/piccolo-orm/piccolo/pull/402>`_.

async first
~~~~~~~~~~~

All of the docs have been updated to show the async version of queries.

For example:

.. code-block:: python

  # Previous:
  Band.select().run_sync()

  # Now:
  await Band.select()

Most people use Piccolo in async apps, and the playground supports top level
await, so you can just paste in ``await Band.select()`` and it will still work.
See `PR 407 <https://github.com/piccolo-orm/piccolo/pull/407>`_.

We decided to use ``await Band.select()`` instead of ``await Band.select().run()``.
Both work, and have their merits, but the simpler version is probably easier
for newcomers.

-------------------------------------------------------------------------------

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

The BlackSheep template generated by ``piccolo asgi new`` now supports mounting
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
* Fixed a bug with migrations and foreign key constraints.

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
