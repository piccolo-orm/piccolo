.. _OneToOne:

One to One
==========

A one to one relationship is basically just a foreign key with a unique
constraint. In Piccolo, you can do it like this:

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Varchar, Text

    class Band(Table):
        name = Varchar()

    class FanClub(Table):
        band = ForeignKey(Band, unique=True)  # note the unique foreign key
        address = Text()

If we have a ``Band`` object:

.. code-block:: python

    band = await Band.objects().where(Band.name == "Pythonistas").first()

To get the associated ``FanClub`` object, you could do this:

.. code-block:: python

    fan_club = await FanClub.objects().where(FanClub.band == band).first()

Or alternatively, using ``get_related``:

.. code-block:: python

    fan_club = await band.get_related(Band.id.join_on(FanClub.band))

    # Alternatively, by reversing the foreign key:
    fan_club = await band.get_related(FanClub.band.reverse())

If doing a select query, and you want data from the related table:

.. code-block:: python

    >>> await Band.select(
    ...     Band.name,
    ...     Band.id.join_on(FanClub.band).address.as_alias("address")
    ... )
    [{'name': 'Pythonistas', 'address': '1 Flying Circus, UK'}, ...]

And filtering by related tables in the ``where`` clause:

.. code-block:: python

    >>> await Band.select(
    ...     Band.name,
    ... ).where(Band.id.join_on(FanClub.band).address.like("%Flying%"))
    [{'name': 'Pythonistas'}]
