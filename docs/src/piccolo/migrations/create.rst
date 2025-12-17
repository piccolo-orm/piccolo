Creating migrations
===================

Migrations are Python files which are used to modify the database schema in a
controlled way. Each migration belongs to a :ref:`Piccolo app <PiccoloApps>`.

You can either manually populate migrations, or allow Piccolo to do it for you
automatically.

We recommend using :ref:`auto migrations <AutoMigrations>` where possible,
as it saves you time.

-------------------------------------------------------------------------------

Manual migrations
-----------------

First, let's create an empty migration:

.. code-block:: bash

    piccolo migrations new my_app

This creates a new migration file in the migrations folder of the app. By
default, the migration filename is the name of the app, followed by a timestamp,
but you can rename it to anything you want:

.. code-block:: bash

    piccolo_migrations/
        my_app_2022_12_06T13_58_23_024723.py

.. note::
    We changed the naming convention for migration files in version ``0.102.0``
    (previously they were like ``2022-12-06T13-58-23-024723.py``). As mentioned,
    the name isn't important - change it to anything you want. The new format
    was chosen because a Python file should start with a letter by convention.

The contents of an empty migration file looks like this:

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager


    ID = "2022-02-26T17:38:44:758593"
    VERSION = "0.69.2" # The version of Piccolo used to create it
    DESCRIPTION = "Optional description"


    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="my_app",
            description=DESCRIPTION
        )

        def run():
            # Replace this with something useful:
            print(f"running {ID}")

        manager.add_raw(run)
        return manager

The ``ID`` is very important - it uniquely identifies the migration, and
shouldn't be changed.

Replace the ``run`` function with whatever you want the migration to do -
typically running some SQL. It can be a function or a coroutine.

Running raw SQL
~~~~~~~~~~~~~~~

If you want to run raw SQL within your migration, you can do so as follows:

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager
    from piccolo.table import Table


    ID = "2025-07-28T09:51:54:296860"
    VERSION = "1.27.1"
    DESCRIPTION = "Updating each band's popularity"


    # This is just a dummy table we use to execute raw SQL with:
    class RawTable(Table):
        pass


    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="my_app",
            description=DESCRIPTION
        )

        #############################################################
        # This will get run when using `piccolo migrations forwards`:

        async def run():
            await RawTable.raw('UPDATE band SET popularity={}', 1000)

        manager.add_raw(run)

        #############################################################
        # If we want to run some code when reversing the migration,
        # using `piccolo migrations backwards`:

        async def run_backwards():
            await RawTable.raw('UPDATE band SET popularity={}', 0)

        manager.add_raw_backwards(run_backwards)

        #############################################################
        # We must always return the MigrationManager:

        return manager

.. hint:: You can learn more about :ref:`raw queries here <Raw>`.

Using your ``Table`` classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the above example, we executed raw SQL, but what if we wanted to use the
``Table`` classes from our project instead?

We have to be quite careful with this. Here's an example:

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager

    # We're importing a table from our project:
    from music.tables import Band


    ID = "2025-07-28T09:51:54:296860"
    VERSION = "1.27.1"
    DESCRIPTION = "Updating each band's popularity"


    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="my_app",
            description=DESCRIPTION
        )

        async def run():
            await Band.update({Band.popularity: 1000}, force=True)

        manager.add_raw(run)
        return manager

We want our migrations to be repeatable - so if someone runs them a year from
now, they will get the same results.

By directly importing our tables, we have the following risks:

* If the ``Band`` class is deleted from the codebase, it could break old
  migrations.
* If we modify the ``Band`` class, perhaps by removing columns, this could also
  break old migrations.

Try and make your migration files independent of other application code, so
they're self contained and repeatable. Even though it goes against `DRY <https://en.wikipedia.org/wiki/Don%27t_repeat_yourself>`_,
it's better to copy the relevant tables into your migration file:

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager
    from piccolo.columns.column_types import Integer
    from piccolo.table import Table


    ID = "2025-07-28T09:51:54:296860"
    VERSION = "1.27.1"
    DESCRIPTION = "Updating each band's popularity"


    # We defined the table within the file, rather than importing it.
    class Band(Table):
        popularity = Integer()


    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="my_app",
            description=DESCRIPTION
        )

        async def run():
            await Band.update({Band.popularity: 1000}, force=True)

        manager.add_raw(run)
        return manager

Another alternative is to use the ``MigrationManager.get_table_from_snapshot``
method to get a table from the migration history. This is very convenient,
especially if the table is large, with many foreign keys.

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager


    ID = "2025-07-28T09:51:54:296860"
    VERSION = "1.27.1"
    DESCRIPTION = "Updating each band's popularity"


    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="",
            description=DESCRIPTION
        )

        async def run():
            # We get a table from the migration history.
            Band = await manager.get_table_from_snapshot(
                app_name="music", table_class_name="Band"
            )
            await Band.update({"popularity": 1000}, force=True)

        manager.add_raw(run)

        return manager

-------------------------------------------------------------------------------

.. _AutoMigrations:

Auto migrations
---------------

Manually writing your migrations gives you a good level of control, but Piccolo
supports `auto migrations` which can save a great deal of time.

Piccolo will work out which tables to add by comparing previous auto migrations,
and your current tables. In order for this to work, you have to register
your app's tables with the ``AppConfig`` in the ``piccolo_app.py`` file at the
root of your app (see :ref:`PiccoloApps`).

Creating an auto migration:

.. code-block:: bash

    piccolo migrations new my_app --auto

.. hint:: Auto migrations are the preferred way to create migrations with
    Piccolo. We recommend using `empty migrations` for special circumstances which
    aren't supported by auto migrations, or to modify the data held in tables, as
    opposed to changing the tables themselves.

.. warning:: Auto migrations for SQLite and MySQL are supported, with limitations.
    SQLite has extremely limited support for SQL ALTER statements and MySQL DDL triggers 
    an implicit commit in transaction and we cannot roll back a DDL using ROLLBACK
    (non-transactional DDL). This might change in the future.

Troubleshooting
~~~~~~~~~~~~~~~

Auto migrations can accommodate most schema changes. There may be some rare edge
cases where a single migration is trying to do too much in one go, and fails.
To avoid these situations, create auto migrations frequently, and keep them
fairly small.

-------------------------------------------------------------------------------

Migration descriptions
----------------------

To make the migrations more memorable, you can give them a description. Inside
the migration file, you can set a ``DESCRIPTION`` global variable manually, or
can specify it when creating the migration:

.. code-block:: bash

    piccolo migrations new my_app --auto --desc="Adding name column"

The Piccolo CLI will then use this description when listing migrations, to make
them easier to identify.
