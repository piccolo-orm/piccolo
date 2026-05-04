Moving a Table Between Piccolo Apps Without Data Loss
======================================================

Piccolo ORM makes it easy to manage models within individual apps. But what if you need to move a table (model) from one app to another—say, from ``app_a`` to ``app_b``—without losing your data?

This tutorial walks you through the safest way to move a table between Piccolo apps using migrations and the ``--fake`` flag.

Use Case
--------

You're working on a project structured with multiple Piccolo apps, and you want to reorganize your models by moving a table (``TableA``) from one app (``app_a``) to another (``app_b``), without affecting the data in your database.

Prerequisites
-------------

- Piccolo ORM installed and configured
- Both ``app_a`` and ``app_b`` listed in ``piccolo_conf.py`` under ``PICCOLO_APPS``
- Basic familiarity with Piccolo migrations

Step-by-Step Instructions
-------------------------

1. Remove the Table from ``app_a``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In ``app_a/tables.py``, delete or comment out the ``TableA`` class definition.

2. Create a Migration in ``app_a``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the following command in your terminal:

.. code-block:: bash

    piccolo migrations new app_a --auto

This will create a migration that removes the table from ``app_a``.

3. Fake Apply the Migration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To prevent the table from actually being dropped from the database, apply the migration using the ``--fake`` flag:

.. code-block:: bash

    piccolo migrations forwards app_a --fake

This marks the migration as applied without making real changes to the database.

4. Move the Table to ``app_b``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Copy the ``TableA`` class definition into ``app_b/tables.py``.

Ensure the definition matches exactly what it was in ``app_a``.

5. Create a Migration in ``app_b``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate a new  fake migration for ``app_b`` to register ``TableA``:

.. code-block:: bash

    piccolo migrations new app_b --auto

6. Apply the Migration in ``app_b``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply the new migration:

.. code-block:: bash

    piccolo migrations forwards app_b --fake

Because the table already exists in the database, Piccolo will associate it with ``app_b`` without duplicating or altering it.

Notes & Tips
------------

- This process preserves your data because it avoids actually dropping or creating the table.
- Always back up your database before doing schema changes.
- Inspect the migration files to understand what Piccolo is tracking.
