Migrate an existing project to Piccolo
======================================

Introduction
------------

If you have an existing project and Postgres database, and you want to use
Piccolo with it, these are the steps you need to take.

Option 1 - ``piccolo asgi new``
-------------------------------

This is the recommended way of creating brand new projects. If this is your
first experience with Piccolo, then it's a good idea to create a test project:

.. code-block:: bash

    mkdir test_project
    cd test_project
    piccolo asgi new

You'll learn a lot about how Piccolo works by looking at the generated code.
You can then copy over the relevant files to your existing project if you like.

Alternatively, doing it from scratch, you'll need to do the following:

Option 2 - from scratch
-----------------------

Create a Piccolo project file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new ``piccolo_conf.py`` file in the root of your project:

.. code-block:: bash

    piccolo project new

This contains your database details, and is used to register Piccolo apps.

Create a new Piccolo app
~~~~~~~~~~~~~~~~~~~~~~~~

The app contains your ``Table`` classes and migrations. Run this command at the
root of your project:

.. code-block:: bash

    # Replace 'my_app' with whatever you want to call your app
    piccolo app new my_app

Register the new Piccolo app
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Register this new app in ``piccolo_conf.py``. For example:

.. code-block:: python

    APP_REGISTRY = AppRegistry(
        apps=[
            "my_app.piccolo_app",
        ]
    )

While you're at it, make sure the database credentials are correct in
``piccolo_conf.py``.

Make ``Table`` classes for your current database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now, if you run:

.. code-block:: bash

    piccolo schema generate

It will output Piccolo ``Table`` classes for your current database. Copy the
output into ``my_app/tables.py``. Double check that everything looks correct.

In ``my_app/piccolo_app.py`` make sure it's tracking these tables for
migration purposes.

.. code-block:: python

    from piccolo.conf.apps import AppConfig, table_finder

    APP_CONFIG = AppConfig(
        table_classes=table_finder(["my_app.tables"], exclude_imported=True),
        ...
    )

Create an initial migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This will create a new file in ``my_app/piccolo_migrations``:

.. code-block:: bash

    piccolo migrations new my_app --auto

These tables already exist in the database, as it's an existing project, so
you need to fake apply this initial migration:

.. code-block:: bash

    piccolo migrations forwards my_app --fake

Making queries
~~~~~~~~~~~~~~

Now you're basically setup - to make database queries:

.. code-block:: python

    from my_app.tables import MyTable

    async def my_endpoint():
        data = await MyTable.select()
        return data

Making new migrations
~~~~~~~~~~~~~~~~~~~~~

Just modify the files in ``tables.py``, and then run:

.. code-block:: bash

    piccolo migrations new my_app --auto
    piccolo migrations forwards my_app
