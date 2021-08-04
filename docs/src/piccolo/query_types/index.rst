Query Types
===========

There are many different queries you can perform using Piccolo.

The main ways to query data are with :ref:`Select`, which returns data as
dictionaries, and :ref:`Objects` , which returns data as class instances, like a
typical ORM.

.. toctree::
    :maxdepth: 1

    ./select
    ./objects
    ./alter  
    ./create_table
    ./delete
    ./exists
    ./insert
    ./raw
    ./update
    ./transactions

Comparisons
-----------

If you're familiar with other ORMs, here are some guides which show the Piccolo
equivalents of common queries.

.. toctree::
    :maxdepth: 1

    ./django_comparison
