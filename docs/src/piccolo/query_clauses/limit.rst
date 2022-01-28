.. _limit:

limit
=====

You can use ``limit`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Rather than returning all of the matching results, it will only return the
number you ask for.

.. code-block:: python

    await Band.select().limit(2)

Likewise, with objects:

.. code-block:: python

    await Band.objects().limit(2)
