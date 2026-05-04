.. _setting_up_postgres:

##############
Setup Postgres
##############

Installation
************

Mac
===

The quickest way to get Postgres up and running on the Mac is using
`Postgres.app <https://postgresapp.com/>`_.

Ubuntu
======

On Ubuntu you can use ``apt``.

.. code-block:: bash

    sudo apt update
    sudo apt install postgresql

-------------------------------------------------------------------------------

Creating a database
*******************

Mac
===

psql
----

Postgres.app should make ``psql`` available for the user who installed it.

.. code-block:: bash

    psql

Enter the following:

.. code-block:: bash

    CREATE DATABASE "my_database_name";

pgAdmin
-------

If you prefer a GUI, pgAdmin has an  `installer available <https://www.pgadmin.org/download/pgadmin-4-macos/>`_.

Ubuntu
======

psql
----

Using ``psql``:

.. code-block:: bash

    sudo su postgres -c psql

Enter the following:

.. code-block:: bash

    CREATE DATABASE "my_database_name";

pgAdmin
-------

DEB packages are available for `Ubuntu <https://www.pgadmin.org/download/pgadmin-4-apt/>`_.

-------------------------------------------------------------------------------

Postgres version
****************

Piccolo is tested on most major Postgres versions (see the `GitHub Actions file <https://github.com/piccolo-orm/piccolo/blob/master/.github/workflows/tests.yaml>`_).
