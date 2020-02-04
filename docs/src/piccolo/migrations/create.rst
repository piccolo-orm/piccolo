Creating migrations
===================

Migrations are used to create and modify tables in the database.

.. code-block:: bash

    piccolo migration new

This creates a migrations folder, along with a migration file.

The migration filename is a timestamp, which also serves as the migration ID.

.. code-block:: bash

    migrations/
        2018-09-04T19:44:09.py

The contents of the migration file look like this:

.. code-block:: python

    ID = '2018-09-04T19:44:09'

    async def forwards():
        pass

    async def backwards():
        pass

Populating the migration
------------------------

At the moment, this migration does nothing when run - we need to populate the
forwards and backwards functions.

.. code-block:: python

    from piccolo.columns import Varchar
    from piccolo.tables import Table


    ID = '2018-09-04T19:44:09'


    class Band(Table):
        name = Varchar(length=100)


    async def forwards():
        transaction = Band._meta.db.transaction()

        transaction.add(
            Band.create_table(),
        )

        await transaction.run()


    async def backwards():
        await Band.alter().drop_table().run()

The golden rule
~~~~~~~~~~~~~~~

Never import your tables directly into a migration, and run methods on them.

This is a **bad example**:

.. code-block:: python

    from ..tables import Band

    ID = '2018-09-04T19:44:09'


    async def forwards():
        transaction = Band._meta.db.transaction()

        transaction.add(
            Band.create_table(),
        )

        await transaction.run()


    async def backwards():
        await Band.alter().drop_table().run()

The reason you don't want to do this, is your tables will change over time. If
someone runs your migrations in the future, they will get different results.
Make your migrations completely independent of other code, so they're
self contained and repeatable.

Running migrations
------------------

When the migration is run, the forwards function is executed. To do this:

.. code-block:: bash

    piccolo migration forwards

Inspect your database, and a ``band`` table should now exist.

Reversing migrations
--------------------

To reverse the migration, run this:

.. code-block:: bash

    piccolo migration backwards 2018-09-04T19:44:09

This executes the backwards function.

You can try going forwards and backwards a few times to make sure it works as
expected.

Altering tables
---------------

To alter tables, you'll use mostly use alter queries (see :ref:`alter`), and
occasionally raw queries (see :ref:`raw`).
