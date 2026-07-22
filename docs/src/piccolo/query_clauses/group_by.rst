.. _group_by:

group_by
========

You can use ``group_by`` clauses with the following queries:

* :ref:`Select`

It is used in combination with the :ref:`aggregate functions <AggregateFunctions>`
- for example, ``Count``.

-------------------------------------------------------------------------------

Count
-----

In the following query, we get a count of the number of bands per manager:

.. code-block:: python

    >>> from piccolo.query.functions.aggregate import Count

    >>> await Band.select(
    ...     Band.manager.name.as_alias('manager_name'),
    ...     Count(alias='band_count')
    ... ).group_by(
    ...     Band.manager.name
    ... )

    [
        {"manager_name": "Graydon", "band_count": 1},
        {"manager_name": "Guido", "band_count": 1}
    ]

-------------------------------------------------------------------------------

Other aggregate functions
-------------------------

These work the same as ``Count``. See :ref:`aggregate functions <AggregateFunctions>`.

-------------------------------------------------------------------------------

``GroupByRaw``
--------------

For more complex cases, use ``GroupByRaw`` to group by a raw SQL expression or
an alias created by ``SelectRaw``. For example:

.. code-block:: python

    from piccolo.query import GroupByRaw, SelectRaw
    from piccolo.query.functions.aggregate import Count

    await Band.select(
        SelectRaw("DATE(created_at) AS created_date"),
        Count(),
    ).group_by(
        GroupByRaw("created_date")
    )

As with other raw query helpers, only use trusted SQL strings.
