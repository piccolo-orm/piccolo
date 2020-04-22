.. _PiccoloApps:

Piccolo Apps
============

By leveraging Piccolo apps you can unlock some useful functionality like auto
migrations.

Creating an app
---------------

Run the following command within your project:

.. code-block:: bash

    piccolo app new my_app


This will create a folder like this:

.. code-block:: bash

    my_app/
        __init__.py
        piccolo_app.py
        piccolo_migrations/
            __init__.py
        tables.py


It's important to register this app with your `piccolo_conf.py` app.

.. code-block:: python

    # piccolo_conf.py
    APP_REGISTRY = AppRegistry(apps=['my_app.piccolo_app'])


Anytime you invoke the `piccolo` command, you will now be able to perform
operations on your app, the most important of which is :ref:`Migrations`.

AppConfig
---------

Inside the `piccolo_app.py` file is an AppConfig instance. This is how you
customise how your app's settings.

.. code-block:: python

    import os

    from piccolo.conf.apps import AppConfig
    from .tables import (
        Author,
        Post,
        Category,
        CategoryToPost,
    )


    CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


    APP_CONFIG = AppConfig(
        app_name='blog',
        migrations_folder_path=os.path.join(CURRENT_DIRECTORY, 'piccolo_migrations'),
        table_classes=[Author, Post, Category, CategoryToPost],
        migration_dependencies=[],
        commands=[]
    )

table_classes
~~~~~~~~~~~~~

Use this to register your app's tables. This is important for auto migrations (see :ref:`Migrations`).

migration_dependencies
~~~~~~~~~~~~~~~~~~~~~~

Used to specify other Piccolo apps whose migrations need to be run before the
current app's migrations.
