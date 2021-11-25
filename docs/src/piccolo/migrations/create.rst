Creating migrations
===================

Migrations are Python files which are used to modify the database schema in a
controlled way. Each migration belongs to a Piccolo app (see :ref:`PiccoloApps`).

You can either manually populate migrations, or allow Piccolo to do it for you
automatically. To create an empty migration:

.. code-block:: bash

    piccolo migrations new my_app

This creates a new migration file in the migrations folder of the app. The
migration filename is a timestamp, which also serves as the migration ID.

.. code-block:: bash

    piccolo_migrations/
        2021-08-06T16-22-51-415781.py

The contents of an empty migration file looks like this:

.. code-block:: python

    from piccolo.apps.migrations.auto.migration_manager import MigrationManager


    ID = '2021-08-06T16:22:51:415781'
    VERSION = "0.29.0" # The version of Piccolo used to create it
    DESCRIPTION = "Optional description"


    async def forwards():
        manager = MigrationManager(migration_id=ID, app_name="my_app", description=DESCRIPTION)

        def run():
            print(f"running {ID}")

        manager.add_raw(run)
        return manager

Replace the ``run`` function with whatever you want the migration to do -
typically running some SQL. It can be a function or a coroutine.

-------------------------------------------------------------------------------

The golden rule
---------------

Never import your tables directly into a migration, and run methods on them.

This is a **bad example**:

.. code-block:: python

    from ..tables import Band

    ID = '2021-08-06T16:22:51:415781'
    VERSION = "0.29.0" # The version of Piccolo used to create it
    DESCRIPTION = "Optional description"


    async def forwards():
        manager = MigrationManager(migration_id=ID)

        async def run():
            await Band.create_table().run()

        manager.add_raw(run)
        return manager

The reason you don't want to do this, is your tables will change over time. If
someone runs your migrations in the future, they will get different results.
Make your migrations completely independent of other code, so they're
self contained and repeatable.

-------------------------------------------------------------------------------

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

.. warning:: Auto migrations aren't supported in SQLite, because of SQLite's
    extremely limited support for SQL Alter statements. This might change in
    the future.

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
