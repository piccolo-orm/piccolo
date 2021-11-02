.. _first:

first
=====

You can use ``first`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Rather than returning a list of results, just the first result is returned.

.. code-block:: python

    >>> Band.select().first().run_sync()
    {'name': 'Pythonistas', 'manager': 1, 'popularity': 1000, 'id': 1}

Likewise, with objects:

.. code-block:: python

    >>> Band.objects().first().run_sync()
    <Band at 0x10fdef1d0>

If no match is found, then ``None`` is returned instead.
