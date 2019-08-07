.. _ExampleSchema:

Example Schema
==============

This is the schema used by the example queries throughout the docs.

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Varchar


    class Manager(Table):
        name = Varchar(max_length=100)


    class Band(Table):
        name = Varchar(max_length=100)
        manager = Varchar(max_length=100)

To understand more about defining your own schemas, see :ref:`DefiningSchema`.
