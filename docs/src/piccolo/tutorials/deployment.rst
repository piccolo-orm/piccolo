Deploying using Docker
======================

Docker
------

`Docker <https://docs.docker.com/>`_ is a very popular way of deploying
applications, using containers.

Base image
~~~~~~~~~~

Piccolo has several dependencies which are compiled (e.g. asyncpg, orjson),
which is great for performance, but you may run into difficulties when using
Alpine Linux as your base Docker image. Alpine uses a different compiler
toolchain to most Linux distros.

It's highly recommended to use Debian as your base Docker image. Many Python packages
have prebuilt versions for Debian, meaning you don't have to compile them at
all during install. The result is a much faster build process, and potentially
even a smaller overall Docker image size (the size of Alpine quickly balloons
after you've added all of the compilation dependencies).

Environment variables
~~~~~~~~~~~~~~~~~~~~~

By using environment variables, we can inject the database credentials for
Piccolo.

Example Dockerfile
~~~~~~~~~~~~~~~~~~

This is a very simple Dockerfile, and illustrates the basics:

.. code-block:: dockerfile

    # Specify the base image:
    FROM python:3.12-bookworm

    # Install the pip requirements:
    RUN pip install --upgrade pip
    ADD app/requirements.txt /
    RUN pip install -r /requirements.txt

    # Add the application code:
    ADD app /app

    # Environment variables:
    ENV PG_HOST=localhost
    ENV PG_PORT=5432
    ENV PG_USER=my_database_user
    ENV PG_PASSWORD=""
    ENV PG_DATABASE=my_database

    CMD ["/usr/local/bin/python", "/app/main.py"]

We can then modify our :ref:`piccolo_conf.py <PiccoloConf>` file to use these
environment variables:

.. code-block:: python

    # piccolo_conf.py

    import os

    DB = PostgresEngine(
        config={
            "port": int(os.environ.get("PG_PORT", "5432")),
            "user": os.environ.get("PG_USER", "my_database_user"),
            "password": os.environ.get("PG_PASSWORD", ""),
            "database": os.environ.get("PG_DATABASE", "my_database"),
            "host": os.environ.get("PG_HOST", "localhost"),
        }
    )

When we run the container (usually via `Kubernetes <https://kubernetes.io/>`_,
`Docker Compose <https://docs.docker.com/compose/>`_, or similar),
we can specify the database credentials using environment variables, which will
be used by our application.

Accessing a local Postgres database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bear in mind that if you have Postgres running locally on the server (i.e. on
``localhost``), your Docker container won't automatically be able to access it.
You can try Docker's host based networking, or just run Postgres within a
Docker container.
