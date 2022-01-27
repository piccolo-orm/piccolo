.. _Exists:

Exists
======

This checks whether any rows exist which match the criteria.

.. code-block:: python

    >>> await Band.exists().where(Band.name == 'Pythonistas')
    True

-------------------------------------------------------------------------------

Query clauses
-------------

where
~~~~~

See :ref:`where`.
