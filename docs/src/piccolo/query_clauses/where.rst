.. _where:

where
=====

You can use ``where`` clauses with the following queries:

* :ref:`Delete`
* :ref:`Exists`
* :ref:`Objects`
* :ref:`Select`
* :ref:`Update`

It allows powerful filtering of your data.

Equal / Not Equal
-----

.. code-block:: python

    b = Band
    b.select().where(
        b.name == 'Pythonistas'
    ).run_sync()

.. code-block:: python

    b = Band
    b.select().where(
        b.name != 'Rustaceans'
    ).run_sync()

Greater than / less than
------------------------

You can use the ``<, >, <=, >=`` operators, which work as you expect.

.. code-block:: python

    b = Band
    b.select().where(
        b.popularity >= 100
    ).run_sync()

like / ilike
-------------

The percentage operator is required to designate where the match should occur.

.. code-block:: python

    b = Band
    b.select().where(
        b.name.like('Py%')  # Matches the start of the string
    ).run_sync()

    b.select().where(
        b.name.like('%istas')  # Matches the end of the string
    ).run_sync()

    b.select().where(
        b.name.like('%is%')  # Matches anywhere in string
    ).run_sync()

``ilike`` is identical, except it's case insensitive.

not_like
--------

Usage is the same as ``like`` excepts it excludes matching rows.

.. code-block:: python

    b = Band
    b.select().where(
        b.name.not_like('Py%')
    ).run_sync()

is_in / not_in
--------------

.. code-block:: python

    b = Band
    b.select().where(
        b.name.is_in(['Pythonistas'])
    ).run_sync()

.. code-block:: python

    b = Band
    b.select().where(
        b.name.not_in(['Rustaceans'])
    ).run_sync()

Complex queries - and / or
---------------------------

You can make complex ``where`` queries using ``&`` for AND, and ``|`` for OR.

.. code-block:: python

    b = Band
    b.select().where(
        (b.popularity >= 100) & (b.popularity < 1000)
    ).run_sync()

    b.select().where(
        (b.popularity >= 100) | (b.name ==  'Pythonistas')
    ).run_sync()

You can make really complex ``where`` clauses if you so choose - just be
careful to include brackets in the correct place.

.. code-block:: python

    ((b.popularity >= 100) & (b.manager.name ==  'Guido')) | (b.popularity > 1000)

Using multiple ``where`` clauses is equivalent to an AND.

.. code-block:: python

    b = Band

    # These are equivalent:
    b.select().where(
        (b.popularity >= 100) & (b.popularity < 1000)
    ).run_sync()

    b.select().where(
        b.popularity >= 100
    ).where(
        b.popularity < 1000
    ).run_sync()
