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

Launches a SQL shell (``psql`` or ``sqlite3`` depending on the engine), using
the connection settings defined in ``piccolo_conf.py``. It's convenient if you
need to run raw SQL queries on your database.

.. code-block:: bash

    piccolo sql_shell run

For it to work, the underlying command needs to be on the path (i.e. ``psql``
or ``sqlite3`` depending on which you're using).

tester
~~~~~~

Launches `pytest <https://pytest.org/>`_ , which runs your unit test suite. The
advantage of using this rather than running ``pytest`` directly, is the
``PICCOLO_CONF`` environment variable will automatically be set before the
testing starts, and will be restored to it's initial value once the tests
finish.

.. code-block:: bash

    piccolo tester run

Setting the :ref:`PICCOLO_CONF<PICCOLO_CONF>` environment variable means your
code will use the database engine specified in that file for the duration of
the testing.

By default ``piccolo tester run`` sets ``PICCOLO_CONF`` to
``'piccolo_conf_test'``, meaning that a file called ``piccolo_conf_test.py``
will be imported.

If you prefer, you can set a custom ``PICCOLO_CONF`` value:

.. code-block:: bash

    piccolo tester run --piccolo_conf=my_custom_piccolo_conf

You can also pass arguments to pytest:

.. code-block:: bash

    piccolo tester run --pytest_args="-s foo"

-------------------------------------------------------------------------------

Optional includes
-----------------

These need to be explicitly registered with your :ref:`AppRegistry<AppRegistry>`.

user
~~~~

Provides a user table, and commands for creating / managing users. See
:ref:`Authentication`.
