.. _returning:

returning
=========

You can use the ``returning`` clause with the following queries:

* :ref:`Insert`
* :ref:`Update`
* :ref:`Delete`

By default, an update query returns an empty list, but using the ``returning``
clause you can retrieve values from the updated rows.

.. code-block:: python

    >>> await Band.update({
    ...     Band.name: 'Pythonistas Tribute Band'
    ... }).where(
    ...     Band.name == 'Pythonistas'
    ... ).returning(Band.id, Band.name)
    [{'id': 1, 'name': 'Pythonistas Tribute Band'}]

Similarly, for an insert query - we can retrieve some of the values from the
inserted rows:

.. code-block:: python

    >>> await Manager.insert(
    ...     Manager(name="Maz"),
    ...     Manager(name="Graydon")
    ... ).returning(Manager.id, Manager.name)

    [{'id': 1, 'name': 'Maz'}, {'id': 1, 'name': 'Graydon'}]

As another example, let's use delete and return the full row(s):

.. code-block:: python

    >>> await Band.delete().where(
    ...     Band.name == "Pythonistas"
    ... ).returning(*Band.all_columns())

    [{'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000}]

By counting the number of elements of the returned list, you can find out
how many rows were affected or processed by the operation.

.. warning:: This works for all versions of Postgres, but only
    `SQLite 3.35.0 <https://www.sqlite.org/lang_returning.html>`_ and above
    support the returning clause. See the :ref:`docs <check_sqlite_version>` on
    how to check your SQLite version. 

    Not supported for MySQL because there is no ``RETURNING`` clause in MySQL.
