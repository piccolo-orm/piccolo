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

    >>> await Band.objects()
    [<Band: 1>, <Band: 2>]

To get certain rows:

.. code-block:: python

    >>> await Band.objects().where(Band.name == 'Pythonistas')
    [<Band: 1>]

To get a single row (or ``None`` if it doesn't exist):

.. code-block:: python

    >>> await Band.objects().get(Band.name == 'Pythonistas')
    <Band: 1>

To get the first row:

.. code-block:: python

    >>> await Band.objects().first()
    <Band: 1>

You'll notice that the API is similar to :ref:`Select` - except it returns all
columns.

-------------------------------------------------------------------------------

Creating objects
----------------

You can pass the column values using kwargs:

.. code-block:: python

    >>> band = Band(name="C-Sharps", popularity=100)
    >>> await band.save()

Alternatively, you can pass in a dictionary, which is friendlier to static
analysis tools like Mypy (it can easily detect typos in the column names):

.. code-block:: python

    >>> band = Band({Band.name: "C-Sharps", Band.popularity: 100})
    >>> await band.save()

We also have this shortcut which combines the above into a single line:

.. code-block:: python

    >>> band = await Band.objects().create(name="C-Sharps", popularity=100)

-------------------------------------------------------------------------------

Updating objects
----------------

Objects have a :meth:`save <piccolo.table.Table.save>` method, which is
convenient for updating values:

.. code-block:: python

    band = await Band.objects().where(
        Band.name == 'Pythonistas'
    ).first()

    band.popularity = 100000

    # This saves all values back to the database.
    await band.save()

    # Or specify specific columns to save:
    await band.save([Band.popularity])

-------------------------------------------------------------------------------

Deleting objects
----------------

Similarly, we can delete objects, using the ``remove`` method.

.. code-block:: python

    band = await Band.objects().where(
        Band.name == 'Pythonistas'
    ).first()

    await band.remove()

-------------------------------------------------------------------------------

Fetching related objects
------------------------

get_related
~~~~~~~~~~~

If you have an object from a table with a :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>`
column, and you want to fetch the related row as an object, you can do so
using ``get_related``.

.. code-block:: python

    band = await Band.objects().where(
        Band.name == 'Pythonistas'
    ).first()

    manager = await band.get_related(Band.manager)
    >>> manager
    <Manager: 1>
    >>> manager.name
    'Guido'

Prefetching related objects
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can also prefetch the rows from related tables, and store them as child
objects. To do this, pass :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>`
columns into ``objects``, which refer to the related rows you want to load.

.. code-block:: python

    band = await Band.objects(Band.manager).where(
        Band.name == 'Pythonistas'
    ).first()

    >>> band.manager
    <Manager: 1>
    >>> band.manager.name
    'Guido'

If you have a table containing lots of ``ForeignKey`` columns, and want to
prefetch them all you can do so using ``all_related``.

.. code-block:: python

    ticket = await Ticket.objects(
        Ticket.concert.all_related()
    ).first()

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
    await ticket.concert.band_1.save()

Instead of passing the :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>`
columns into the ``objects`` method, you can use the ``prefetch`` clause if you
prefer.

.. code-block:: python

    # These are equivalent:
    ticket = await Ticket.objects(
        Ticket.concert.all_related()
    ).first()

    ticket = await Ticket.objects().prefetch(
        Ticket.concert.all_related()
    ).first()

-------------------------------------------------------------------------------

get_or_create
-------------

With ``get_or_create`` you can get an existing record matching the criteria,
or create a new one with the ``defaults`` arguments:

.. code-block:: python

    band = await Band.objects().get_or_create(
        Band.name == 'Pythonistas', defaults={Band.popularity: 100}
    )

    # Or using string column names
    band = await Band.objects().get_or_create(
        Band.name == 'Pythonistas', defaults={'popularity': 100}
    )

You can find out if an existing row was found, or if a new row was created:

.. code-block:: python

    band = await Band.objects.get_or_create(
        Band.name == 'Pythonistas'
    )
    band._was_created  # True if it was created, otherwise False if it was already in the db

Complex where clauses are supported, but only within reason. For example:

.. code-block:: python

    # This works OK:
    band = await Band.objects().get_or_create(
        (Band.name == 'Pythonistas') & (Band.popularity == 1000),
    )

    # This is problematic, as it's unclear what the name should be if we
    # need to create the row:
    band = await Band.objects().get_or_create(
        (Band.name == 'Pythonistas') | (Band.name == 'Rustaceans'),
        defaults={'popularity': 100}
    )

-------------------------------------------------------------------------------

to_dict
-------

If you need to convert an object into a dictionary, you can do so using the
``to_dict`` method.

.. code-block:: python

    band = await Band.objects().first()

    >>> band.to_dict()
    {'id': 1, 'name': 'Pythonistas', 'manager': 1, 'popularity': 1000}

If you only want a subset of the columns, or want to use aliases for some of
the columns:

.. code-block:: python

    band = await Band.objects().first()

    >>> band.to_dict(Band.id, Band.name.as_alias('title'))
    {'id': 1, 'title': 'Pythonistas'}

-------------------------------------------------------------------------------

refresh
-------

If you have an object which has gotten stale, and want to refresh it, so it
has the latest data from the database, you can use the
:meth:`refresh <piccolo.table.Table.refresh>` method.

.. code-block:: python

    # If we have an instance:
    band = await Band.objects().first()

    # And it has gotten stale, we can refresh it:
    await band.refresh()

    # Or just refresh certain columns:
    await band.refresh([Band.name])

It works with ``prefetch`` too:

.. code-block:: python

    # If we have an instance with a child object:
    band = await Band.objects(Band.manager).first()

    # And it has gotten stale, we can refresh it:
    await band.refresh()

    # The nested object will also be updated if it was stale:
    >>> band.manager.name
    "New value"

``refresh`` is very useful in unit tests:

.. code-block:: python

    # If we have an instance:
    band = await Band.objects().where(Band.name == "Pythonistas").first()

    # Call an API endpoint which updates the object (e.g. with httpx):
    await client.patch(f"/band/{band.id}/", json={"popularity": 5000})

    # Make sure the instance was updated:
    await band.refresh()
    assert band.popularity == 5000

-------------------------------------------------------------------------------

Query clauses
-------------

batch
~~~~~

See :ref:`batch`.

callback
~~~~~~~~

See :ref:`callback`.

first
~~~~~

See :ref:`first`.

limit
~~~~~

See :ref:`limit`.

offset
~~~~~~

See :ref:`offset`.

order_by
~~~~~~~~

See :ref:`order_by`.

output
~~~~~~

See :ref:`output`.

where
~~~~~

See :ref:`Where` .
