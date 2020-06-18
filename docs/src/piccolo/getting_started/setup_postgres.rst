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

Piccolo is currently tested against Postgres 9.6, 10.6, and 11.1 so it's
recommended to use one of those. To check all supported versions, see the
`Travis file <https://github.com/piccolo-orm/piccolo/blob/master/.travis.yml>`_.

-------------------------------------------------------------------------------

What about other databases?
***************************

At the moment the focus is on providing the best Postgres experience possible,
along with some SQLite support. Other databases may be supported in the future.
