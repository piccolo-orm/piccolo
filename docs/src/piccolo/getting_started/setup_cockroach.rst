.. _setting_up_cockroach:

###############
Setup Cockroach
###############

Installation
************

Follow the  `instructions for your OS <https://www.cockroachlabs.com/docs/stable/install-cockroachdb.html>`_.


Versions
--------

We support the latest stable version.

.. note::
   Features using ``format()`` will be available in v22.2 or higher, but we recommend using the stable version so you can upgrade automatically when it becomes generally available.

   Cockroach is designed to be a "rolling database": Upgrades are as simple as switching out to the next version of a binary (or changing a number in a ``docker-compose.yml``). This has one caveat: You cannot upgrade an "alpha" release. It is best to stay on the latest stable.


-------------------------------------------------------------------------------

Creating a database
*******************

cockroach sql
-------------

CockroachDB comes with its own management tooling.

.. code-block:: bash

    cd ~/wherever/you/installed/cockroachdb
    cockroach sql --insecure

Enter the following:

.. code-block:: bash

    create database piccolo;
    use piccolo;

Management GUI
--------------

CockroachDB comes with its own web-based management GUI available on localhost: http://127.0.0.1:8080/

Beekeeper Studio
----------------

If you prefer a GUI, Beekeeper Studio is recommended and has an  `installer available <https://www.beekeeperstudio.io/>`_.


-------------------------------------------------------------------------------


Column Types
************

As of this writing, CockroachDB will always convert ``JSON`` to ``JSONB`` and will always report ``INTEGER`` as ``BIGINT``.

Piccolo will automatically handle these special cases for you, but we recommend being explicit about this to prevent complications in future versions of Piccolo.

* Use ``JSONB()`` instead of ``JSON()``
* Use ``BigInt()`` instead of ``Integer()``
