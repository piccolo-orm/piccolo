What is Piccolo?
================

Piccolo is a fast, easy to learn ORM and query builder.

Some of it's stand out features are:

* Support for :ref:`sync and async <SyncAndAsync>`.
* A builtin :ref:`playground <Playground>`, which makes learning a breeze.
* Fully type annotated, with great :ref:`tab completion support <tab_completion>` - it works great with
  `iPython <https://ipython.org/>`_ and `VSCode <https://code.visualstudio.com/>`_.
* Batteries included - a :ref:`User model and authentication <Authentication>`,
  :ref:`migrations <migrations>`, an :ref:`admin <ecosystem>`, and more.
* Templates for creating your own :ref:`ASGI web app <ASGICommand>`.

History
-------

Piccolo was created while working at a design agency, where almost all projects
being undertaken were API driven (often with high traffic), and required
web sockets. The author was naturally interested in the possibilities of :mod:`asyncio`.
Piccolo is built from the ground up with asyncio in mind. Likewise, Piccolo
makes extensive use of :mod:`type annotations <typing>`, another innovation in
Python around the time Piccolo was started.

A really important thing when working at a design agency is having a **great
admin interface**. A huge amount of effort has gone into
`Piccolo Admin <https://piccolo-orm.readthedocs.io/en/latest/index.html>`_
to make something you'd be proud to give to a client.

A lot of batteries are included because Piccolo is a pragmatic framework
focused on delivering quality, functional apps to customers. This is why we have
templating tools like ``piccolo asgi new`` for getting a web app started
quickly, automatic database migrations for making iteration fast, and lots of
authentication middleware and endpoints for rapidly
`building APIs <https://piccolo-api.readthedocs.io/en/latest/>`_ out of the box.

Piccolo has been used extensively by the author on professional projects, for
a range of corporate and startup clients.
