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
-----------------

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

-------------------------------------------------------------------------------

Greater than / less than
------------------------

You can use the ``<, >, <=, >=`` operators, which work as you expect.

.. code-block:: python

    b = Band
    b.select().where(
        b.popularity >= 100
    ).run_sync()

-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------

not_like
--------

Usage is the same as ``like`` excepts it excludes matching rows.

.. code-block:: python

    b = Band
    b.select().where(
        b.name.not_like('Py%')
    ).run_sync()

-------------------------------------------------------------------------------

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

-------------------------------------------------------------------------------

is_null / is_not_null
---------------------

These queries work, but some linters will complain about doing a comparison
with None:

.. code-block:: python

    b = Band

    # Fetch all bands with a manager
    b.select().where(
        b.manager != None
    ).run_sync()

    # Fetch all bands without a manager
    b.select().where(
        b.manager == None
    ).run_sync()

To avoid the linter errors, you can use `is_null` and `is_not_null` instead.

.. code-block:: python

    b = Band

    # Fetch all bands with a manager
    b.select().where(
        b.manager.is_not_null()
    ).run_sync()

    # Fetch all bands without a manager
    b.select().where(
        b.manager.is_null()
    ).run_sync()

-------------------------------------------------------------------------------

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

Using And / Or directly
~~~~~~~~~~~~~~~~~~~~~~~

Rather than using the ``|`` and ``&`` characters, you can use the ``And`` and
``Or`` classes, which are what's used under the hood.

.. code-block:: python

    from piccolo.columns.combination import And, Or

    b = Band

    b.select().where(
        Or(
            And(b.popularity >= 100, b.popularity < 1000),
            b.name == 'Pythonistas'
        )
    ).run_sync()

-------------------------------------------------------------------------------

WhereRaw
--------

In certain situations you may want to have raw SQL in your where clause.

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    Band.select().where(
        WhereRaw("name = 'Pythonistas'")
    ).run_sync()

It's important to parameterise your SQL statements if the values come from an
untrusted source, otherwise it could lead to a SQL injection attack.

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    value = "Could be dangerous"

    Band.select().where(
        WhereRaw("name = {}", value)
    ).run_sync()

``WhereRaw`` can be combined into complex queries, just as you'd expect:

.. code-block:: python

    from piccolo.columns.combination import WhereRaw

    b = Band
    b.select().where(
        WhereRaw("name = 'Pythonistas'") | (b.popularity > 1000)
    ).run_sync()
