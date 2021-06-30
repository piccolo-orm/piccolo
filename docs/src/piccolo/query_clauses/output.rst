.. _output:

output
======

You can use ``output`` clauses with the following queries:

* :ref:`Select`
* :ref:`Objects`

-------------------------------------------------------------------------------

Select queries only
-------------------

as_json
~~~~~~~

To return the data as a JSON string:

.. code-block:: python

    >>> Band.select().output(as_json=True).run_sync()
    '[{"name":"Pythonistas","manager":1,"popularity":1000,"id":1},{"name":"Rustaceans","manager":2,"popularity":500,"id":2}]'

Piccolo can use `orjson <https://github.com/ijl/orjson>`_ for JSON serialisation,
which is blazing fast, and can handle most Python types, including dates,
datetimes, and UUIDs. To install Piccolo with orjson support use
``pip install piccolo[orjson]``.

as_list
~~~~~~~

If you're just querying a single column from a database table, you can use
``as_list`` to flatten the results into a single list.

.. code-block:: python

    >>> Band.select(Band.id).output(as_list=True).run_sync()
    [1, 2]

-------------------------------------------------------------------------------

Select and Objects queries
--------------------------

load_json
~~~~~~~~~

If querying JSON or JSONB columns, you can tell Piccolo to deserialise the JSON
values automatically.

.. code-block:: python

    >>> RecordingStudio.select().output(load_json=True).run_sync()
    [{'id': 1, 'name': 'Abbey Road', 'facilities': {'restaurant': True, 'mixing_desk': True}}]

    >>> studio = RecordingStudio.objects().first().output(load_json=True).run_sync()
    >>> studio.facilities
    {'restaurant': True, 'mixing_desk': True}
