Testing
=======

Piccolo provides a few tools to make testing easier.

-------------------------------------------------------------------------------

Test runner
-----------

Piccolo ships with a handy command for running your unit tests using pytest.
See the :ref:`tester app<TesterApp>`.

You can put your test files anywhere you like, but a good place is in a ``tests``
folder within your Piccolo app. The test files should be named like
``test_*. py`` or ``*_test.py`` for pytest to recognise them.

-------------------------------------------------------------------------------

Model Builder
-------------

When writing unit tests, it's usually required to have some data seeded into
the database. You can build and save the records manually or use
:class:`ModelBuilder <piccolo.testing.model_builder.ModelBuilder>` to generate
random records for you.

This way you can randomize the fields you don't care about and specify
important fields explicitly and reduce the amount of manual work required.
``ModelBuilder`` currently supports all Piccolo column types and features.

Let's say we have the following schema:

.. code-block:: python

    from piccolo.columns import ForeignKey, Varchar

    class Manager(Table):
        name = Varchar(length=50)

    class Band(Table):
        name = Varchar(length=50)
        manager = ForeignKey(Manager, null=True)

You can build a random ``Band`` which will also build and save a random
``Manager``:

.. code-block:: python

    from piccolo.testing.model_builder import ModelBuilder

    # Band instance with random values persisted:
    band = await ModelBuilder.build(Band)

.. note:: ``ModelBuilder.build(Band)`` persists the record into the database by default.

You can also run it synchronously if you prefer:

.. code-block:: python

    manager = ModelBuilder.build_sync(Manager)


To specify any attribute, pass the ``defaults`` dictionary to the ``build`` method:

.. code-block:: python

    manager = ModelBuilder.build(Manager)

    # Using table columns:
    band = await ModelBuilder.build(
        Band,
        defaults={Band.name: "Guido", Band.manager: manager}
    )

    # Or using strings as keys:
    band = await ModelBuilder.build(
        Band,
        defaults={"name": "Guido", "manager": manager}
    )

To build objects without persisting them into the database:

.. code-block:: python

    band = await ModelBuilder.build(Band, persist=False)

To build objects with minimal attributes, leaving nullable fields empty:

.. code-block:: python

    # Leaves manager empty:
    band = await ModelBuilder.build(Band, minimal=True)

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

    from unittest import TestCase

    from piccolo.apps.migrations.commands.backwards import run_backwards
    from piccolo.apps.migrations.commands.forwards import run_forwards
    from piccolo.utils.sync import run_sync

    class TestApp(TestCase):
        def setUp(self):
            run_sync(run_forwards("all"))

        def tearDown(self):
            run_sync(run_backwards("all", auto_agree=True))

        def test_app(self):
            # Do some testing ...
            pass

-------------------------------------------------------------------------------

Testing async code
------------------

There are a few options for testing async code using pytest.

You can either call any async code using Piccolo's ``run_sync`` utility:

.. code-block:: python

    from piccolo.utils.sync import run_sync

    async def get_data():
        ...

    def test_get_data():
        rows = run_sync(get_data())
        assert len(rows) == 1

Alternatively, you can make your tests natively async.

If you prefer using pytest's function based tests, then take a look at
`pytest-asyncio <https://github.com/pytest-dev/pytest-asyncio>`_. Simply
install it using ``pip install pytest-asyncio``, then you can then write tests
like this:

.. code-block:: python

    async def test_select():
        rows = await MyTable.select()
        assert len(rows) == 1

If you prefer class based tests, and are using Python 3.8 or above, then have
a look at :class:`IsolatedAsyncioTestCase <unittest.IsolatedAsyncioTestCase>`
from Python's standard library. You can then write tests like this:

.. code-block:: python

    from unittest import IsolatedAsyncioTestCase

    class MyTest(IsolatedAsyncioTestCase):
        async def test_select(self):
            rows = await MyTable.select()
            assert len(rows) == 1
