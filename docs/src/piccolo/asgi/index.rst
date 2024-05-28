.. _ASGICommand:

####
ASGI
####

Using Piccolo standalone is fine if you want to build a data science script,
but often you'll want to build a web application around it.

`ASGI <https://asgi.readthedocs.io/en/latest/>`_  is a standardised way for
async Python libraries to interoperate. It's the equivalent of WSGI in the
synchronous world.

By using the ``piccolo asgi new`` command, Piccolo will scaffold an ASGI web
app for you, which includes everything you need to get started. The command
will ask for your preferences on which libraries to use.

-------------------------------------------------------------------------------

Routing frameworks
******************

Currently, `Starlette <https://www.starlette.io/>`_, `FastAPI <https://fastapi.tiangolo.com/>`_,
`BlackSheep <https://www.neoteroi.dev/blacksheep/>`_,
`Litestar <https://litestar.dev/>`_, `Esmerald <https://esmerald.dev/>`_ and
`Lilya <https://lilya.dev/>`_ are supported.

Other great ASGI routing frameworks exist, and may be supported in the future
(`Quart <https://pgjones.gitlab.io/quart/>`_ ,
`Sanic <https://sanic.readthedocs.io/en/latest/>`_ ,
`Django <https://www.djangoproject.com/>`_  etc).

Which to use?
=============

All are great choices. FastAPI is built on top of Starlette and Esmerald is built on top of Lilya, so they're
very similar. FastAPI, BlackSheep and Esmerald are great if you want to document a REST
API, as they have built-in OpenAPI support.

-------------------------------------------------------------------------------

Web servers
************

`Hypercorn <https://pgjones.gitlab.io/hypercorn/>`_ and
`Uvicorn <https://www.uvicorn.org/>`_  are available as ASGI servers.
`Daphne <https://github.com/django/daphne>`_ can't be used programatically so
was omitted at this time.
