FastAPI
=======

`FastAPI <https://fastapi.tiangolo.com/>`_ is a popular ASGI web framework. The
purpose of this tutorial is to give some hints on how to get started with
Piccolo and FastAPI.

Piccolo and FastAPI are a great match, and are commonly used together.

Creating a new project
----------------------

Using the ``piccolo asgi new`` command, Piccolo will scaffold a new FastAPI for
you - simple!

Pydantic models
---------------

FastAPI uses `Pydantic <https://docs.pydantic.dev/>`_ for serialising and
deserialising data.

Piccolo provides :func:`create_pydantic_model <piccolo.utils.pydantic.create_pydantic_model>`
which created Pydantic models for you based on your Piccolo tables.

Of course, you can also just define your Pydantic models by hand.

Transactions
------------

Using FastAPI's dependency injection system, we can easily wrap each endpoint
in a transaction.

.. literalinclude:: fastapi_src/app.py
    :emphasize-lines: 19-21,36

FastAPI dependencies can be declared at the endpoint, ``APIRouter``, or even
app level.

``FastAPIWrapper``
------------------

Piccolo API has a powerful utility called
:class:`FastAPIWrapper <piccolo_api.fastapi.endpoints.FastAPIWrapper>` which
generates REST endpoints based on your Piccolo tables, and adds them to FastAPI's
Swagger docs. It's a very productive way of building an API.

Authentication
--------------

`Piccolo API <https://piccolo-api.readthedocs.io/en/latest/>`_ ships with
`authentication middleware <https://piccolo-api.readthedocs.io/en/latest/which_authentication/index.html>`_
which is compatible with `FastAPI middleware <https://fastapi.tiangolo.com/tutorial/middleware/>`_.
