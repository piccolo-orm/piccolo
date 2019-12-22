.. _Objects:

Objects
=======

When doing :ref:`Select`  queries, you get data back in the form of a list of
dictionaries (where each dictionary represents a row).

This is useful in a lot of situations, but it's also useful to get objects
back instead.

In Piccolo, an instance of a Table represents a row. Lets do an
example.

.. code-block:: python

    # To get all objects:
    Band.objects().run_sync()

    # To get certain rows:
    Band.objects().where(Band.name == 'Pythonistas').run_sync()

    # Get the first row
    Band.objects().first().run_sync()

You'll notice that the API is similar to `select` - except it returns all
columns.

Saving objects
--------------

Objects have a `save` method, which is convenient for updating values:

.. code-block:: python

    # To get certain rows:
    pythonistas = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    pythonistas.popularity = 100000
    pythonistas.save().run_sync()

Deleting objects
----------------

Similarly, we can delete objects, using the `remove` method.

.. code-block:: python

    # To get certain rows:
    pythonistas = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    pythonistas.remove().run_sync()

get_related
-----------

If you have an object with a foreign key, and you want to fetch the related
object, you can do so using ``get_related``.

.. code-block:: python

    pythonistas = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    manager = pythonistas.get_related(Band.manager).run_sync()
    >>> print(manager.name)
    'Guido'

Query clauses
-------------

batch
~~~~~~~

See :ref:`batch`.

limit
~~~~~

See  :ref:`limit`.

offset
~~~~~~

See  :ref:`offset`.

first
~~~~~

See  :ref:`first`.

order_by
~~~~~~~~

See  :ref:`order_by`.

where
~~~~~

See :ref:`Where` .
