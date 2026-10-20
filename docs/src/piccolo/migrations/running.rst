Running migrations
==================

.. hint:: To see all available options for these commands, use the ``--help``
    flag, for example ``piccolo migrations forwards --help``.

Forwards
--------

When the migration is run, the forwards function is executed. To do this:

.. code-block:: bash

    piccolo migrations forwards my_app

Multiple apps
~~~~~~~~~~~~~

If you have multiple apps you can run them all using:

.. code-block:: bash

    piccolo migrations forwards all

Migration table
~~~~~~~~~~~~~~~

When running the migrations, Piccolo will automatically create a database table
called ``migration`` if it doesn't already exist. Each time a migration is
succesfully ran, a new row is added to this table.

.. _FakeMigration:

Fake
~~~~

We can 'fake' running a migration - we record that it ran in the database
without actually running it.

There are two ways to do this - by passing in the ``--fake`` flag on the
command line:

.. code-block:: bash

    piccolo migrations forwards my_app 2022-09-04T19:44:09 --fake

Or by setting ``fake=True`` on the ``MigrationManager`` within the migration
file.

.. code-block:: python

    async def forwards():
        manager = MigrationManager(
            migration_id=ID,
            app_name="app",
            description=DESCRIPTION,
            fake=True
        )
        ...


This is useful if we started from an existing database using
``piccolo schema generate``, and the initial migration we generated is for
tables which already exist, hence we fake run it.

-------------------------------------------------------------------------------

Reversing migrations
--------------------

To reverse the migration, run the following command, specifying the ID of a
migration:

.. code-block:: bash

    piccolo migrations backwards my_app 2022-09-04T19:44:09

Piccolo will then reverse the migrations for the given app, starting with the
most recent migration, up to and including the migration with the specified ID.

You can try going forwards and backwards a few times to make sure it works as
expected.

-------------------------------------------------------------------------------

Preview
-------

To see the SQL queries of a migration without actually running them, use the
``--preview`` flag.

This works when running migrations forwards:

.. code-block:: bash

    piccolo migrations forwards my_app --preview

Or backwards:

.. code-block:: bash

    piccolo migrations backwards 2022-09-04T19:44:09 --preview

-------------------------------------------------------------------------------

Checking migrations
-------------------

You can easily check which migrations have and haven't ran using the following:

.. code-block:: bash

    piccolo migrations check

-------------------------------------------------------------------------------

Source
------

These are the underlying Python functions which are called, so you can see
all available options. These functions are convered into a CI using
`targ <http://targ.readthedocs.io/>`_.

.. currentmodule:: piccolo.apps.migrations.commands.forwards

.. autofunction:: forwards

.. currentmodule:: piccolo.apps.migrations.commands.backwards

.. autofunction:: backwards

.. currentmodule:: piccolo.apps.migrations.commands.check

.. autofunction:: check
