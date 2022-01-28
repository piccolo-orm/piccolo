.. _SyncAndAsync:

Sync and Async
==============

One of the motivations for making Piccolo was the lack of ORMs and query
builders which support asyncio.

Piccolo is designed to be async first. However, you can use Piccolo in
synchronous apps as well, whether that be a WSGI web app, or a data science
script.

-------------------------------------------------------------------------------

Async example
-------------

You can await a query to run it:

.. code-block:: python

    >>> await Band.select(Band.name)
    [{'name': 'Pythonistas'}]

Alternatively, you can await a query's ``run`` method:

.. code-block:: python

    # This makes it extra explicit that a database query is being made:
    >>> await Band.select(Band.name).run()

    # It also gives you more control over how the query is run.
    # For example, if we wanted to bypass the connection pool for some reason:
    >>> await Band.select(Band.name).run(in_pool=False)

Using the async version is useful for applications which require high
throughput. Piccolo makes building an ASGI web app really simple - see
:ref:`ASGICommand`.

-------------------------------------------------------------------------------

Sync example
------------

This lets you execute a query in an application which isn't using asyncio:

.. code-block:: python

    >>> Band.select(Band.name).run_sync()
    [{'name': 'Pythonistas'}]

-------------------------------------------------------------------------------

Explicit
--------

By using ``await`` and ``run_sync``, it makes it very explicit when a query is
actually being executed.

Until you execute ``await`` or ``run_sync``, you can chain as many methods onto your
query as you like, safe in the knowledge that no database queries are being
made.
