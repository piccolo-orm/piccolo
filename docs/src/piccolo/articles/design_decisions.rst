Design Decisions
================

As close as possible to SQL
---------------------------

The classes / methods / functions in Piccolo mirror their SQL counterparts as
closely as possible.

For example:

 * In other ORMs, you define models - in Piccolo you define tables.
 * Rather than using a filter method, you use a `where` method like in SQL.

Get the SQL at any time
-----------------------

At any time you can access the __str__ method of a query, to see the
underlying SQL - making the ORM feel less magic.

.. code-block:: python

    query = Band.select().columns(Band.name).where(Band.popularity >= 100)

    print(query)
    'SELECT name from band where popularity > 100'
