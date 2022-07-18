.. _returning:

returning
=========

You can use the ``returning`` clause with the following queries:

* :ref:`Insert`
* :ref:`Update`

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

.. warning:: This works for all versions of Postgres, but only
    `SQLite 3.35.0 <https://www.sqlite.org/lang_returning.html>`_ and above
    support the returning clause. See the :ref:`docs <check_sqlite_version>` on
    how to check your SQLite version.
