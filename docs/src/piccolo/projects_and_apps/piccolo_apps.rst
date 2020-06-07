.. _PiccoloApps:

Piccolo Apps
============

By leveraging Piccolo apps you can:

 * Modularise your code.
 * Share your apps with other Piccolo users.
 * Unlock some useful functionality like auto migrations.

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


It's important to register your new app with the ``APP_REGISTRY`` in
`piccolo_conf.py`.

.. code-block:: python

    # piccolo_conf.py
    APP_REGISTRY = AppRegistry(apps=['my_app.piccolo_app'])


Anytime you invoke the `piccolo` command, you will now be able to perform
operations on your app, such as :ref:`Migrations`.

AppConfig
---------

Inside your app's `piccolo_app.py` file is an ``AppConfig`` instance. This is
how you customise your app's settings.

.. code-block:: python

    # piccolo_app.py
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

app_name
~~~~~~~~

This is used to identify your app, when using the `piccolo` CLI, for example:

.. code-block:: bash

    piccolo migrations forwards blog

migrations_folder_path
~~~~~~~~~~~~~~~~~~~~~~

Specifies where your app's migrations are stored. By default, a folder called
`piccolo_migrations` is used.

table_classes
~~~~~~~~~~~~~

Use this to register your app's tables. This is important for auto migrations (see :ref:`Migrations`).

migration_dependencies
~~~~~~~~~~~~~~~~~~~~~~

Used to specify other Piccolo apps whose migrations need to be run before the
current app's migrations.

commands
~~~~~~~~

You can register functions and coroutines, which are automatically added to
the `piccolo` CLI.

The `targ <http://targ.readthedocs.io/>`_ library is used under the hood. It
makes it really easy to write command lines tools - just use type annotations
and docstrings. Here's an example:

.. code-block:: python

    def say_hello(name: str):
        """
        Say hello.

        :param name:
            The person to greet.

        """
        print(name)

We then register it with the `AppConfig`.

.. code-block:: python

    # piccolo_app.py

    APP_CONFIG = AppConfig(
        # ...
        commands=[say_hello]
    )

And from the command line:

.. code-block:: bash

    >>> piccolo my_app say_hello bob
    bob

By convention, store the command definitions in a `commands` folder in your
app.

.. code-block:: bash

    my_app/
        __init__.py
        piccolo_app.py
        commands/
            __init__.py
            say_hello.py

Piccolo itself is bundled with several apps - have a look at the source code
for inspiration.

Sharing Apps
------------

By breaking up your project into apps, the project becomes more maintainable.
You can also share these apps between projects, and they can even be installed
using pip.
