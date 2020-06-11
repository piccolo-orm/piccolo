.. _SyncAndAsync:

Sync and Async
==============

One of the main motivations for making Piccolo was the lack of options for
ORMs which support asyncio.

However, you can use Piccolo in synchronous apps as well, whether that be a
WSGI web app, or a data science script.

Sync example
------------

.. code-block:: python

    from my_schema import Band


    def main():
        print(Band.select().run_sync())


    if __name__ == '__main__':
        main()

Async example
-------------

.. code-block:: python

    import asyncio
    from my_schema import Band


    async def main():
        print(await Band.select().run())


    if __name__ == '__main__':
        asyncio.run(main())

Which to use?
-------------

A lot of the time, using the sync version works perfectly fine. Many of the
examples use the sync version.

Using the async version is useful for web applications which require high
throughput, based on `ASGI frameworks <https://piccolo-orm.com/blog/introduction-to-asgi>`_.
Piccolo makes building an ASGI web app really simple - see :ref:`ASGICommand`.

Explicit
--------

By using ``run`` and ``run_sync``, it makes it very explicit when a query is
actually being executed.

Until you execute one of those methods, you can chain as many methods onto your
query as you like, safe in the knowledge that no database queries are being
made.
