.. _having:

having
======

You can use the ``having`` clause with the following queries:

* :ref:`Select`

It is used in combination with the :ref:`group_by` clause, to filter the
grouped rows.

The syntax is identical to the :ref:`where` clause.

-------------------------------------------------------------------------------

Example
-------

In the following example, we get the number of albums per band (filtering out
any bands with less than 2 albums).

.. hint:: You can run this query in the :ref:`playground`.

.. code-block:: python

    >>> from piccolo.query.functions.aggregate import Count

    >>> await Album.select(
    ...     Album.band.name.as_alias('band_name'),
    ...     Count()
    ... ).group_by(
    ...     Album.band
    ... ).having(
    ...     Count() >= 2
    ... )

    [
        {"band_name": "Pythonistas", "count": 2},
    ]
