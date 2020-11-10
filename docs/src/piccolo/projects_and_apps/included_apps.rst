Included Apps
=============

Just as you can modularise your own code using :ref:`apps<PiccoloApps>`, Piccolo itself
ships with several builtin apps, which provide a lot of its functionality.

Auto includes
-------------

The following are registered with your :ref:`AppRegistry<AppRegistry>` automatically:

app
~~~

Lets you create new Piccolo apps. See :ref:`PiccoloApps`.

.. code-block:: bash

    piccolo app new

asgi
~~~~

Lets you scaffold an ASGI web app. See :ref:`ASGICommand`.

.. code-block:: bash

    piccolo asgi new

meta
~~~~

Tells you which version of Piccolo is installed.

.. code-block:: bash

    piccolo meta version

migrations
~~~~~~~~~~

Lets you create and run migrations. See :ref:`Migrations`.

playground
~~~~~~~~~~

Lets you learn the Piccolo query syntax, using an example schema. See
:ref:`Playground`.

.. code-block:: bash

    piccolo playground run

project
~~~~~~~

Lets you create a new ``piccolo_conf.py`` file. See :ref:`PiccoloProjects`.

.. code-block:: bash

    piccolo project new

shell
~~~~~

Launches an iPython shell, and automatically imports all of your registered
``Table`` classes. It's great for running adhoc database queries using Piccolo.

.. code-block:: bash

    piccolo shell run

sql_shell
~~~~~~~~~

Launches a SQL shell (``psql`` or ``sqlite`` depending on the engine), using
the connection settings defined in ``piccolo_conf.py``. It's convenient if you
need to run raw SQL queries on your database.

.. code-block:: bash

    piccolo sql_shell run

For it to work, the underlying command needs to be on the path (i.e. ``psql``
or ``sqlite`` depending on which you're using).

-------------------------------------------------------------------------------

Optional includes
-----------------

These need to be explicitly registered with your :ref:`AppRegistry<AppRegistry>`.

user
~~~~

Provides a user table, and commands for creating / managing users. See
:ref:`Authentication`.
