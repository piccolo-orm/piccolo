.. _Playground:

Playground
==========

Piccolo ships with a handy command called `playground`, which is a great way
to learn the basics.

.. code-block:: bash

    piccolo playground

It will create an example schema for you (see :ref:`ExampleSchema`) , populates it with data, and launches an `iPython <https://ipython.org/>`_ shell.

You can follow along with the tutorials without first learning advanced
concepts like migrations.

It's a nice place to experiment with querying / inserting / deleting data using
Piccolo, no matter how experienced you are.

.. warning::
    Each time you launch the playground it flushes out the existing tables and rebuilds them, so don't use it for anything permanent!

SQLite
------

SQLite is used by default, which provides a zero config way of getting started.

A ``piccolo.sqlite`` file will get created in the current directory.

Advanced usage
---------------

To see how to use the playground with Postgres, and other advanced usage, see
:ref:`PlaygroundAdvanced`.

Test queries
------------

The schema generated in the playground represents fictional bands and their
concerts.

When the playground is started it prints out the available tables.

Give these queries a go:

.. code-block:: python

    Band.select().run_sync()
    Band.objects().run_sync()
    Band.select().columns(Band.name).run_sync()
    Band.select().columns(Band.name, Band.manager.name).run_sync()

Tab completion is your friend
-----------------------------

Piccolo was designed to make tab completion available in as many situations
as possible. Use it to find the column names for a table (e.g. ``Band.name``),
and the different query types (e.g. ``Band.select``).

Using tab completion will help avoid errors, and speed up your coding.
