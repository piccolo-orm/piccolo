.. _PiccoloProjects:

Piccolo Projects
================

A Piccolo project is a collection of apps.

-------------------------------------------------------------------------------

piccolo_conf.py
---------------

A project requires a ``piccolo_conf.py`` file. To create this, use the following command:

.. code-block:: bash

    piccolo project new

The file serves two important purposes:

* Contains your database settings.
* Is used for registering :ref:`PiccoloApps`.

Location
~~~~~~~~

By convention, the ``piccolo_conf.py`` file should be at the root of your project:

.. code-block::

    my_project/
        piccolo_conf.py
        my_app/
            piccolo_app.py

This means that when you use the ``piccolo`` CLI from the ``my_project``
folder it can import ``piccolo_conf.py``.

If you prefer to keep ``piccolo_conf.py`` in a different location, or to give
it a different name, you can do so using the ``PICCOLO_CONF`` environment
variable (see :ref:`PICCOLO_CONF<PICCOLO_CONF>`). For example:

.. code-block::

    my_project/
        conf/
            piccolo_conf_local.py
        my_app/
            piccolo_app.py

.. code-block:: bash

    export PICCOLO_CONF=conf.piccolo_conf_local

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
