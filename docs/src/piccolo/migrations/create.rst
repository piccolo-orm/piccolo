Creating migrations
===================

Migrations are used to create the tables in the database.

.. code-block:: bash

    piccolo new

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

    from ..tables import Band

    ID = '2018-09-04T19:44:09'


    async def forwards():
        transaction = Band.Meta.db.transaction()

        transaction.add(
            Band.create_without_columns(),

            Band.alter().add_column(
                'name',
                Varchar(length=100)
            ),
        )

        await transaction.run()


    async def backwards():
        await Band.drop().run()

Running migrations
------------------

When the migration is run, the forwards function is executed. To do this:

.. code-block:: bash

    piccolo forwards

Inspect your database, and a ``band`` table should now exist.

Reversing migrations
--------------------

To reverse the migration, run this:

.. code-block:: bash

    piccolo backwards 2018-09-04T19:44:09

This executes the backwards function.

You can try going forwards and backwards a few times to make sure it works as
expected.
