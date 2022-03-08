.. _ExampleSchema:

Example Schema
==============

This is the schema used by the example queries throughout the docs, and also
in the :ref:`playground<Playground>`.

``Manager`` and ``Band`` are most commonly used:

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Integer, Varchar


    class Manager(Table):
        name = Varchar(length=100)


    class Band(Table):
        name = Varchar(length=100)
        manager = ForeignKey(references=Manager)
        popularity = Integer()

We sometimes use these other tables in the examples too:

.. code-block:: python

    class Venue(Table):
        name = Varchar()
        capacity = Integer()


    class Concert(Table):
        band_1 = ForeignKey(references=Band)
        band_2 = ForeignKey(references=Band)
        venue = ForeignKey(references=Venue)
        starts = Timestamp()
        duration = Interval()


    class Ticket(Table):
        concert = ForeignKey(references=Concert)
        price = Numeric()


    class RecordingStudio(Table):
        name = Varchar()
        facilities = JSONB()

To understand more about defining your own schemas, see :ref:`DefiningSchema`.
