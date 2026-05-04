Datetime functions
==================

.. currentmodule:: piccolo.query.functions.datetime

Postgres / Cockroach
--------------------

Extract
~~~~~~~

.. autoclass:: Extract


SQLite
------

Strftime
~~~~~~~~

.. autoclass:: Strftime


Database agnostic
-----------------

These convenience functions work consistently across database engines.

They all work very similarly, for example:

.. code-block:: python

    >>> from piccolo.query.functions import Year
    >>> await Concert.select(
    ...     Year(Concert.starts, alias="start_year")
    ... )
    [{"start_year": 2024}]

Year
~~~~

.. autofunction:: Year

Month
~~~~~

.. autofunction:: Month

Day
~~~

.. autofunction:: Day

Hour
~~~~

.. autofunction:: Hour

Minute
~~~~~~

.. autofunction:: Minute

Second
~~~~~~

.. autofunction:: Second
