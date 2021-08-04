.. _Aggregate functions:

Aggregate functions
===================

Count
-----

Returns the number of rows which match the query.

.. code-block:: python

    >>> Band.count().where(Band.name == 'Pythonistas').run_sync()
    1


Avg
---

Returns average of numeric rows which match the query.

.. code-block:: python

    >>> from piccolo.query import Avg
    >>> response = Band.select(Avg(Band.popularity)).first().run_sync()
    >>> response["avg"]
    750.0


Sum
---

Returns sum of numeric rows which match the query.

.. code-block:: python

    >>> from piccolo.query import Sum
    >>> response = Band.select(Sum(Band.popularity)).first().run_sync()
    >>> response["sum"]
    1500

Max
---

Returns maximum of rows which match the query.

.. code-block:: python

    >>> from piccolo.query import Max
    >>> response = Band.select(Max(Band.popularity)).first().run_sync()
    >>> response["max"]
    1000

Min
---

Returns minimum of rows which match the query.

.. code-block:: python

    >>> from piccolo.query import Min
    >>> response = Band.select(Min(Band.popularity)).first().run_sync()
    >>> response["min"]
    500

Additional features
-------------------

You also can chain multiple different aggregate functions in one query

.. code-block:: python

    >>> from piccolo.query import Avg, Sum
    >>> response = Band.select(Avg(Band.popularity), Sum(Band.popularity)).first().run_sync()
    >>> response
    {"avg": 750.0, "sum": 1500}

or use aliases for aggregate functions like this.

.. code-block:: python

    >>> from piccolo.query import Avg
    >>> response = Band.select(Avg(Band.popularity, alias="popularity_avg")).first().run_sync()
    >>> response["popularity_avg"]
    750.0


Query clauses
-------------

where
~~~~~

See :ref:`where`.

