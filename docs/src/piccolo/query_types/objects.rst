.. _Objects:

Objects
=======

When doing :ref:`Select`  queries, you get data back in the form of a list of
dictionaries (where each dictionary represents a row). This is useful in a lot
of situations, but it's sometimes preferable to get objects back instead, as we
can manipulate them, and save the changes back to the database.

In Piccolo, an instance of a ``Table`` class represents a row. Let's do some
examples.

-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------

Creating objects
----------------

.. code-block:: python

    >>> band = Band(name="C-Sharps", popularity=100)
    >>> band.save().run_sync()

This can also be done like this:

.. code-block:: python

    >>> band.objects().create(name="C-Sharps", popularity=100).run_sync()

-------------------------------------------------------------------------------

Updating objects
----------------

Objects have a ``save`` method, which is convenient for updating values:

.. code-block:: python

    band = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    band.popularity = 100000
    band.save().run_sync()

-------------------------------------------------------------------------------

Deleting objects
----------------

Similarly, we can delete objects, using the ``remove`` method.

.. code-block:: python

    band = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    band.remove().run_sync()

-------------------------------------------------------------------------------

Fetching related objects
------------------------

get_related
~~~~~~~~~~~

If you have an object from a table with a ``ForeignKey`` column, and you want
to fetch the related row as an object, you can do so using ``get_related``.

.. code-block:: python

    band = Band.objects().where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    manager = band.get_related(Band.manager).run_sync()
    >>> manager
    <Manager: 1>
    >>> manager.name
    'Guido'

Prefetching related objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also prefetch the rows from related tables, and store them as child
objects. To do this, pass ``ForeignKey`` columns into ``objects``, which
refer to the related rows you want to load.

.. code-block:: python

    band = Band.objects(Band.manager).where(
        Band.name == 'Pythonistas'
    ).first().run_sync()

    >>> band.manager
    <Manager: 1>
    >>> band.manager.name
    'Guido'

If you have a table containing lots of ``ForeignKey`` columns, and want to
prefetch them all you can do so using ``all_related``.

.. code-block:: python

    ticket = Ticket.objects(
        Ticket.concert.all_related()
    ).first().run_sync()

    # Any intermediate objects will also be loaded:
    >>> ticket.concert
    <Concert: 1>

    >>> ticket.concert.band_1
    <Band: 1>
    >>> ticket.concert.band_2
    <Band: 2>

You can manipulate these nested objects, and save the values back to the
database, just as you would expect:

.. code-block:: python

    ticket.concert.band_1.name = 'Pythonistas 2'
    ticket.concert.band_1.save().run_sync()

Instead of passing the ``ForeignKey`` columns into the ``objects`` method, you
can use the ``prefetch`` clause if you prefer.

.. code-block:: python

    # These are equivalent:
    ticket = Ticket.objects(
        Ticket.concert.all_related()
    ).first().run_sync()

    ticket = Ticket.objects().prefetch(
        Ticket.concert.all_related()
    ).run_sync()

-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------

to_dict
-------

If you need to convert an object into a dictionary, you can do so using the
``to_dict`` method.

.. code-block:: python

    band = Band.objects().first().run_sync()

    >>> band.to_dict()
    {'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000}

If you only want a subset of the columns, or want to use aliases for some of
the columns:

.. code-block:: python

    band = Band.objects().first().run_sync()

    >>> band.to_dict(Band.id, Band.name.as_alias('title'))
    {'id': 1, 'title': 'Pythonistas'}

-------------------------------------------------------------------------------

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
