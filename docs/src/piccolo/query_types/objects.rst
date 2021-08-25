.. _Objects:

Objects
=======

When doing :ref:`Select`  queries, you get data back in the form of a list of
dictionaries (where each dictionary represents a row). This is useful in a lot
of situations, but it's sometimes preferable to get objects back instead, as we
can manipulate them, and save the changes back to the database.

In Piccolo, an instance of a ``Table`` class represents a row. Let's do some
examples.

Fetching objects
----------------

To get all objects:

.. code-block:: python

    >>> Band.objects().run_sync()
    [<Band: 1>, <Band: 2>]

To get certain rows:

.. code-block:: python

    >>> Band.objects().where(Band.name == 'Pythonistas').run_sync()
    [<Band: 1>]

To get a single row (or ``None`` if it doesn't exist):

.. code-block:: python

    >>> Band.objects().get(Band.name == 'Pythonistas').run_sync()
    <Band: 1>

To get the first row:

.. code-block:: python

    >>> Band.objects().first().run_sync()
    <Band: 1>

You'll notice that the API is similar to :ref:`Select` - except it returns all
columns.

Creating objects
----------------

.. code-block:: python

    >>> band = Band(name="C-Sharps", popularity=100)
    >>> band.save().run_sync()

Updating objects
----------------

Objects have a ``save`` method, which is convenient for updating values:

.. code-block:: python

    pythonistas = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    pythonistas.popularity = 100000
    pythonistas.save().run_sync()

Deleting objects
----------------

Similarly, we can delete objects, using the ``remove`` method.

.. code-block:: python

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

get_or_create
-------------

With ``get_or_create`` you can get an existing record matching the criteria,
or create a new one with the ``defaults`` arguments:

.. code-block:: python

    band = Band.objects().get_or_create(
        Band.name == 'Pythonistas', defaults={Band.popularity: 100}
    ).run_sync()

    # Or using string column names
    band = Band.objects().get_or_create(
        Band.name == 'Pythonistas', defaults={'popularity': 100}
    ).run_sync()

You can find out if an existing row was found, or if a new row was created:

.. code-block:: python

    band = Band.objects.get_or_create(
        Band.name == 'Pythonistas'
    ).run_sync()
    band._was_created  # True if it was created, otherwise False if it was already in the db

Complex where clauses are supported, but only within reason. For example:

.. code-block:: python

    # This works OK:
    band = Band.objects().get_or_create(
        (Band.name == 'Pythonistas') & (Band.popularity == 1000),
    ).run_sync()

    # This is problematic, as it's unclear what the name should be if we
    # need to create the row:
    band = Band.objects().get_or_create(
        (Band.name == 'Pythonistas') | (Band.name == 'Rustaceans'),
        defaults={'popularity': 100}
    ).run_sync()


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

output
~~~~~~

See  :ref:`output`.

where
~~~~~

See :ref:`Where` .
