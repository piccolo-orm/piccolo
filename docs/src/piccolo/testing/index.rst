Testing
=======

Piccolo provides a few tools to make testing easier and decrease manual work.

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

Test runner
-----------

See the :ref:`tester app<TesterApp>`.
