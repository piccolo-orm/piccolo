.. _offset:

offset
======

You can use ``offset`` clauses with the following queries:

* :ref:`Objects`
* :ref:`Select`

This will omit the first X rows from the response.

It's highly recommended to use it along with an :ref:`order_by` clause,
otherwise the results returned could be different each time.

.. code-block:: python

    >>> await Band.select(Band.name).offset(1).order_by(Band.name)
    [{'name': 'Pythonistas'}, {'name': 'Rustaceans'}]

Likewise, with objects:

.. code-block:: python

    >>> await Band.objects().offset(1).order_by(Band.name)
    [Band2, Band3]
