.. _ExampleSchema:

Example Schema
==============

This is the schema used by the example queries throughout the docs.

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Integer, Varchar


    class Manager(Table):
        name = Varchar(length=100)


    class Band(Table):
        name = Varchar(length=100)
        manager = ForeignKey(references=Manager)
        popularity = Integer()

To understand more about defining your own schemas, see :ref:`DefiningSchema`.
