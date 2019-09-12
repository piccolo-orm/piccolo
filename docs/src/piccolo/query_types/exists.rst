.. _Exists:

Exists
======

This checks whether any rows exist which match the criteria.

.. code-block:: python

    >>> Band.exists().where(Band.name == 'Pythonistas').run_sync()
    True

Query clauses
-------------

where
~~~~~

See :ref:`where`.
