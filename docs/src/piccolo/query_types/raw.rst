.. _Raw:

Raw
===

Should you need to, you can execute raw SQL.

.. code-block:: python

    >>> await Band.raw('SELECT name FROM band')
    [{'name': 'Pythonistas'}]

It's recommended that you parameterise any values. Use curly braces ``{}`` as
placeholders:

.. code-block:: python

    >>> await Band.raw('SELECT * FROM band WHERE name = {}', 'Pythonistas')
    [{'name': 'Pythonistas', 'manager': 1, 'popularity': 1000, 'id': 1}]

.. warning:: Be careful to avoid SQL injection attacks. Don't add any user submitted data into your SQL strings, unless it's parameterised.


-------------------------------------------------------------------------------

Query clauses
-------------

batch
~~~~~

See :ref:`batch`.
