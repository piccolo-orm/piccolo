.. _Raw:

Raw
===

Should you need to, you can execute raw SQL.

.. code-block:: python

    >>> Band.raw('select * from band').run_sync()
    [{'name': 'Pythonistas', 'manager': 1, 'popularity': 1000, 'id': 1},
        {'name': 'Rustaceans', 'manager': 2, 'popularity': 500, 'id': 2}]

It's recommended that you parameterise any values. Use curly braces ``{}`` as
placeholders:

.. code-block:: python

    >>> Band.raw('select * from band where name = {}', 'Pythonistas').run_sync()
    [{'name': 'Pythonistas', 'manager': 1, 'popularity': 1000, 'id': 1}]

.. warning:: Be careful to avoid SQL injection attacks. Don't add any user submitted data into your SQL strings, unless it's parameterised.
