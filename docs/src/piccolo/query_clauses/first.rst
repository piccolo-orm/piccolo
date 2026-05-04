.. _first:

first
=====

You can use ``first`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

Rather than returning a list of results, just the first result is returned.

.. code-block:: python

    >>> await Band.select().first()
    {'name': 'Pythonistas', 'manager': 1, 'popularity': 1000, 'id': 1}

Likewise, with objects:

.. code-block:: python

    >>> await Band.objects().first()
    <Band: 1>

If no match is found, then ``None`` is returned instead.
