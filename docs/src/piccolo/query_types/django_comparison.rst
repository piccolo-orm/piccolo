.. _DjangoComparison:

Django Comparison
=================

Here are some common queries, showing how they're done in Django vs Piccolo.
All of the Piccolo examples can also be run :ref:`asynchronously<SyncAndAsync>`.

-------------------------------------------------------------------------------

Queries
-------

get
~~~

They are very similar, except Django raises an ``ObjectDoesNotExist`` exception
if no match is found, whilst Piccolo returns ``None``.

.. code-block:: python

    # Django
    >>> Band.objects.get(name="Pythonistas")
    <Band: 1>
    >>> Band.objects.get(name="DOESN'T EXIST")  # ObjectDoesNotExist!

    # Piccolo
    >>> Band.objects().get(Band.name == 'Pythonistas').run_sync()
    <Band: 1>
    >>> Band.objects().get(Band.name == "DOESN'T EXIST").run_sync()
    None


get_or_create
~~~~~~~~~~~~~

.. code-block:: python

    # Django
    band, created = Band.objects.get_or_create(name="Pythonistas")
    >>> band
    <Band: 1>
    >>> created
    True

    # Piccolo
    >>> band = Band.objects().get_or_create(Band.name == 'Pythonistas').run_sync()
    >>> band
    <Band: 1>
    >>> band._was_created
    True


create
~~~~~~

.. code-block:: python

    # Django
    >>> band = Band(name="Pythonistas")
    >>> band.save()
    >>> band
    <Band: 1>

    # Piccolo
    >>> band = Band(name="Pythonistas")
    >>> band.save().run_sync()
    >>> band
    <Band: 1>

update
~~~~~~

.. code-block:: python

    # Django
    >>> band = Band.objects.get(name="Pythonistas")
    >>> band
    <Band: 1>
    >>> band.name = "Amazing Band"
    >>> band.save()

    # Piccolo
    >>> band = Band.objects().get(Band.name == 'Pythonistas').run_sync()
    >>> band
    <Band: 1>
    >>> band.name = "Amazing Band"
    >>> band.save().run_sync()

delete
~~~~~~

Individual rows:

.. code-block:: python

    # Django
    >>> band = Band.objects.get(name="Pythonistas")
    >>> band.delete()

    # Piccolo
    >>> band = Band.objects().get(Band.name == 'Pythonistas').run_sync()
    >>> band.remove().run_sync()

In bulk:

.. code-block:: python

    # Django
    >>> Band.objects.filter(popularity__lt=1000).delete()

    # Piccolo
    >>> Band.delete().where(Band.popularity < 1000).run_sync()

filter
~~~~~~

.. code-block:: python

    # Django
    >>> Band.objects.filter(name="Pythonistas")
    [<Band: 1>]

    # Piccolo
    >>> Band.objects().where(Band.name == "Pythonistas").run_sync()
    [<Band: 1>]

values_list
~~~~~~~~~~~

.. code-block:: python

    # Django
    >>> Band.objects.values_list('name')
    [{'name': 'Pythonistas'}, {'name': 'Rustaceans'}]

    # Piccolo
    >>> Band.select(Band.name).run_sync()
    [{'name': 'Pythonistas'}, {'name': 'Rustaceans'}]

With ``flat=True``:

.. code-block:: python

    # Django
    >>> Band.objects.values_list('name', flat=True)
    ['Pythonistas', 'Rustaceans']

    # Piccolo
    >>> Band.select(Band.name).output(as_list=True).run_sync()
    ['Pythonistas', 'Rustaceans']

select_related
~~~~~~~~~~~~~~

Django has an optimisation called ``select_related`` which reduces the number
of SQL queries required when accessing related objects.

.. code-block:: python

    # Django
    band = Band.objects.get(name='Pythonistas')
    >>> band.manager  # This triggers another db query
    <Manager: 1>

    # Django, with select_related
    band = Band.objects.select_related('manager').get(name='Pythonistas')
    >>> band.manager  # Manager is pre-cached, so there's no extra db query
    <Manager: 1>

Piccolo has something similar:

.. code-block:: python

    # Piccolo
    band = Band.objects(Band.manager).get(Band.name == 'Pythonistas').run_sync()
    >>> band.manager
    <Manager: 1>

-------------------------------------------------------------------------------

Schema
------

OneToOneField
~~~~~~~~~~~~~

Django has a ``OneToOneField``. It's basically just a foreign key with a unique
constraint. In Piccolo you can achieve it like this:

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Varchar, Text

    class Band(Table):
        name = Varchar()

    class FanClub(Table):
        band = ForeignKey(Band, unique=True)
        address = Text()

If we have a ``Band`` object:

.. code-block:: python

    band = await Band.objects().where(Band.name == "Pythonistas")

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

-------------------------------------------------------------------------------

Database settings
-----------------

In Django you configure your database in ``settings.py``. With Piccolo, you
define an ``Engine`` in ``piccolo_conf.py``. See :ref:`Engines`.

-------------------------------------------------------------------------------

Creating a new project
----------------------

With Django you use ``django-admin startproject mysite``.

In Piccolo you use ``piccolo asgi new`` (see :ref:`ASGICommand`).
