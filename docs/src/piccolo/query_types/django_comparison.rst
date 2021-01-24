.. _DjangoComparison:

Django Comparison
=================

Here are some common queries, showing how they're done in Django vs Piccolo.
All of the Piccolo examples can also be run :ref:`asynchronously<SyncAndAsync>`.

Queries
-------

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
    >>> band = Band.objects().where(Band.name == 'Pythonistas').first().run_sync()
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
    >>> band = Band.objects().where(Band.name == 'Pythonistas').first().run_sync()
    >>> band.remove().run_sync()

In bulk:

.. code-block:: python

    # Django
    >>> Band.objects.filter(popularity__lt=1000).delete()

    # Piccolo
    >>> Band.delete().where(Band.popularity < 1000).delete().run_sync()

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

-------------------------------------------------------------------------------

Database Settings
-----------------

In Django you configure your database in ``settings.py``. With Piccolo, you
define an ``Engine`` in ``piccolo_conf.py``. See :ref:`Engines`.
