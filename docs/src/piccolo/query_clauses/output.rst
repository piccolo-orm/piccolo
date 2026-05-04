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

    >>> await Band.select(Band.name).output(as_json=True)
    '[{"name":"Pythonistas"}]'

Piccolo can use `orjson <https://github.com/ijl/orjson>`_ for JSON serialisation,
which is blazing fast, and can handle most Python types, including dates,
datetimes, and UUIDs. To install Piccolo with orjson support use
``pip install 'piccolo[orjson]'``.

as_list
~~~~~~~

If you're just querying a single column from a database table, you can use
``as_list`` to flatten the results into a single list.

.. code-block:: python

    >>> await Band.select(Band.id).output(as_list=True)
    [1, 2]

nested
~~~~~~

Output any data from related tables in nested dictionaries.

.. code-block:: python

    >>> await Band.select(Band.name, Band.manager.name).first().output(nested=True)
    {'name': 'Pythonistas', 'manager': {'name': 'Guido'}}

-------------------------------------------------------------------------------

Select and Objects queries
--------------------------

.. _load_json:

load_json
~~~~~~~~~

If querying :class:`JSON <piccolo.columns.column_types.JSON>` or :class:`JSONB <piccolo.columns.column_types.JSONB>`
columns, you can tell Piccolo to deserialise the JSON values automatically.

.. code-block:: python

    >>> await RecordingStudio.select().output(load_json=True)
    [{'id': 1, 'name': 'Abbey Road', 'facilities': {'restaurant': True, 'mixing_desk': True}}]

    >>> studio = await RecordingStudio.objects().first().output(load_json=True)
    >>> studio.facilities
    {'restaurant': True, 'mixing_desk': True}
