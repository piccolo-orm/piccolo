.. _callback:

callback
========

You can use ``callback`` clauses with the following queries:

* :ref:`Select`
* :ref:`Objects`

Callbacks are used to run arbitrary code after a query completes.

Callback handlers
-----------------

A callback handler is a function or coroutine that takes query results as
its only parameter.

For example, you can automatically print the result of a select query using
``print`` as a callback handler:

.. code-block:: python

    >>> await Band.select(Band.name).callback(print)
    [{'name': 'Pythonistas'}]

Likewise for an objects query:

.. code-block:: python

    >>> await Band.objects().callback(print)
    [<Band: 1>]

Transforming results
--------------------

Callback handlers are able to modify the results of a query by returning a
value. Note that in the previous examples, the queries returned ``None`` since
``print`` itself returns ``None``.

To modify query results with a custom callback handler:

.. code-block:: python

    >>> def uppercase_name(band):
            return band.name.upper()

    >>> await Band.objects().first().callback(uppercase_name)
    'PYTHONISTAS'

Multiple callbacks
------------------

You can add as many callbacks to a query as you like. This can be done in two
ways.

Passing a list of callbacks:

.. code-block:: python

    Band.select(Band.name).callback([handler_a, handler_b])

Chaining ``callback`` clauses:

.. code-block:: python

    Band.select(Band.name).callback(handler_a).callback(handler_b)

