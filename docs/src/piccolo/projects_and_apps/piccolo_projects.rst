.. _PiccoloProjects:

Piccolo Projects
================

A Piccolo project is a collection of apps.

-------------------------------------------------------------------------------

piccolo_conf.py
---------------

A project requires a ``piccolo_conf.py`` file. To create this file, use the following command:

.. code-block:: bash

    piccolo project new

The file serves two important purposes:

 * Contains your database settings
 * Is used for registering :ref:`PiccoloApps`.

If your ``piccolo_conf.py`` is not in the default location or uses a different name consider:

.. code-block:: bash

    export PICCOLO_CONF=<path/to/new/piccolo_conf.py>

This can be useful if an application is run from outside the application directory such as ``uvicorn app.app:app``.

-------------------------------------------------------------------------------

Example
-------

Here's an example:

.. code-block:: python

    from piccolo.engine.postgres import PostgresEngine


    from piccolo.conf.apps import AppRegistry


    DB = PostgresEngine(
        config={
            "database": "piccolo_project",
            "user": "postgres",
            "password": "",
            "host": "localhost",
            "port": 5432,
        }
    )


    APP_REGISTRY = AppRegistry(
        apps=["home.piccolo_app", "piccolo_admin.piccolo_app"]
    )

-------------------------------------------------------------------------------

DB
--

The DB setting is an ``Engine`` instance. To learn more Engines, see
:ref:`Engines`.

-------------------------------------------------------------------------------

.. _AppRegistry:

APP_REGISTRY
------------

The ``APP_REGISTRY`` setting is an ``AppRegistry`` instance.

.. currentmodule:: piccolo.conf.apps

.. autoclass:: AppRegistry
