UUID v7 support
===============

.. note:: CockroachDB does not currently support UUID v7.

With Postgres 18 and above, UUID v7 is natively supported.

For this to work in older versions of Postgres, a function has to be registered
in the database.


The easiest option is to add the following to :class:`PostgresEngine <piccolo.engines.postgres.PostgresEngine>`:

.. code-block:: python

    DB = PostgresEngine(
        polyfills=['uuid7'],
        ...
    )

Which will try and register a ``uuid7`` function on initialisation.

Alternatives
------------

If you'd rather, you can register an extension such as `pg_uuidv7 <https://github.com/fboulnois/pg_uuidv7>`_.
