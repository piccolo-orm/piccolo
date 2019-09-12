.. _limit:

limit
=====

You can use ``limit`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Rather than returning a list of results, it will only return the number you ask
for.

.. code-block:: python

    Band.select().limit(2).run_sync()

Likewise, with objects:

.. code-block:: python

    Band.objects().limit(2).run_sync()
