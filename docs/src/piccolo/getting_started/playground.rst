.. _Playground:

Playground
==========

Piccolo ships with a handy command called ``playground``, which is a great way
to learn the basics.

.. code-block:: bash

    piccolo playground run

It will create an :ref:`example schema <ExampleSchema>` for you, populates it
with data, and launches an `iPython <https://ipython.org/>`_ shell.

You can follow along with the tutorials without first learning advanced
concepts like migrations.

It's a nice place to experiment with querying / inserting / deleting data using
Piccolo, no matter how experienced you are.

.. warning::
   Each time you launch the playground it flushes out the existing tables and
   rebuilds them, so don't use it for anything permanent!

-------------------------------------------------------------------------------

SQLite
------

SQLite is used by default, which provides a zero config way of getting started.

A ``piccolo.sqlite`` file will get created in the current directory.

-------------------------------------------------------------------------------

Advanced usage
---------------

To see how to use the playground with Postgres or Cockroach, and other
advanced usage, see :ref:`PlaygroundAdvanced`.

-------------------------------------------------------------------------------

Test queries
------------

The schema generated in the playground represents fictional bands and their
concerts.

When the playground is started it prints out the available tables.

Give these queries a go:

.. code-block:: python

    await Band.select()
    await Band.objects()
    await Band.select(Band.name)
    await Band.select(Band.name, Band.manager.name)

-------------------------------------------------------------------------------

Tab completion is your friend
-----------------------------

Piccolo was designed to make tab completion available in as many situations
as possible. Use it to find the column names for a table (e.g. ``Band.name``),
and the different query types (e.g. ``Band.select``).

Using tab completion will help avoid errors, and speed up your coding.
