.. _UUIDColumnsMigrationTutorial:

UUID columns in Piccolo >= 1.31.0
=================================

Prior to ``piccolo==1.31.0``, Postgres
:class:`UUID<piccolo.columns.column_types.UUID>` columns generated their
default values using ``uuid_generate_v4()``, which is part of the
``uuid-ossp`` extension.

In all the versions of Posgres that Piccolo supports, there is now a
``gen_random_uuid()`` function built in, which Piccolo now uses for all new
``UUID`` columns for generating default values in the database.

Your existing ``UUID`` columns will be left alone, and will continue to use the
``uuid-ossp`` extension.

Note that :class:`PostgresEngine<piccolo.engine.postgres.PostgresEngine>` has
an ``extensions`` argument. These are Postgres extensions which Piccolo will
try to enable when starting up. This used to include ``uuid-ossp`` by default,
but this is no longer the case. If you want to maintain the old behaviour,
simply do this:

.. code-block:: python

    DB = PostgresEngine(extensions=['uuid-ossp'])

If you want to migrate an existing ``UUID`` column over to use
``gen_random_uuid()`` then run this script:

.. code-block:: sql

    ALTER TABLE my_table ALTER COLUMN my_uuid_column SET DEFAULT gen_random_uuid();
