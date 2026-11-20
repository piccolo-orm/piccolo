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

QueryString
-----------

For more flexibility, you can pass a
:class:`QueryString <piccolo.querystring.QueryString>` to ``raw``.
``QueryString`` objects can be nested, and values are always passed to the
database as parameters. You can also include other Piccolo queries within a
``QueryString``. For example, to count the rows returned by a ``select``:

.. code-block:: python

    from piccolo.querystring import QueryString

    >>> await Band.raw(
    ...     QueryString(
    ...         "SELECT COUNT(*) AS total FROM ({}) AS sub",
    ...         Band.select(Band.name).where(Band.popularity > 500),
    ...     )
    ... )
    [{'total': 1}]

.. note:: Only queries which consist of a single SQL statement can be nested
    within a ``QueryString``.

.. warning:: Be careful to avoid SQL injection attacks. Don't add any user submitted data into your SQL strings, unless it's parameterised.


-------------------------------------------------------------------------------

Query clauses
-------------

batch
~~~~~

See :ref:`batch`.
