Testing
=======

Piccolo provides a few tools to make testing easier and decrease manual work.

-------------------------------------------------------------------------------

Model Builder
-------------

When writing unit tests, it's usually required to have some data seeded into the database.
You can build and save the records manually or use ``ModelBuilder`` to generate random records for you.

This way you can randomize the fields you don't care about and specify important fields explicitly and
reduce the amount of manual work required.
``ModelBuilder`` currently supports all Piccolo column types and features.

Let's say we have the following schema:

.. code-block:: python

    from piccolo.columns import ForeignKey, Varchar

    class Manager(Table):
        name = Varchar(length=50)

    class Band(Table):
        name = Varchar(length=50)
        manager = ForeignKey(Manager, null=True)

You can build a random ``Band`` which will also build and save a random ``Manager``:

.. code-block:: python

    from piccolo.testing.model_builder import ModelBuilder

    band = await ModelBuilder.build(Band)  # Band instance with random values persisted

.. note:: ``ModelBuilder.build(Band)`` persists record into the database by default.

You can also run it synchronously if you prefer:

.. code-block:: python

    manager = ModelBuilder.build_sync(Manager)


To specify any attribute, pass the ``defaults`` dictionary to the ``build`` method:

.. code-block:: python

    manager = ModelBuilder.build(Manager)

    # Using table columns
    band = await ModelBuilder.build(Band, defaults={Band.name: "Guido", Band.manager: manager})

    # Or using strings as keys
    band = await ModelBuilder.build(Band, defaults={"name": "Guido", "manager": manager})

To build objects without persisting them into the database:

.. code-block:: python

    band = await ModelBuilder.build(Band, persist=False)

To build object with minimal attributes, leaving nullable fields empty:

.. code-block:: python

    band = await ModelBuilder.build(Band, minimal=True)  # Leaves manager empty

-------------------------------------------------------------------------------

Test runner
-----------

This runs your unit tests using pytest. See the :ref:`tester app<TesterApp>`.

-------------------------------------------------------------------------------

Creating the test schema
------------------------

When running your unit tests, you usually start with a blank test database,
create the tables, and then install test data.

To create the tables, there are a few different approaches you can take. Here
we use ``create_tables`` and ``drop_tables``:

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

Alternatively, you can run the migrations to setup the schema if you prefer:

.. code-block:: python

    import asyncio
    from unittest import TestCase

    from piccolo.apps.migrations.commands.backwards import run_backwards
    from piccolo.apps.migrations.commands.forwards import run_forwards

    class TestApp(TestCase):
        def setUp(self):
            asyncio.run(run_forwards("all"))

        def tearDown(self):
            asyncio.run(run_backwards("all", auto_agree=True))

        def test_app(self):
            # Do some testing ...
            pass
