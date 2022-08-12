Running migrations
==================

.. hint:: To see all available options for these commands, use the ``--help``
    flag, for example ``piccolo migrations forwards --help``.
.. hint:: To see the SQL queries of a migration without actually running them , use the ``--preview``
    flag, for example: ``piccolo migrations forwards my_app --preview``  or  ``piccolo migrations backwards 2018-09-04T19:44:09 --preview``.

Forwards
--------

When the migration is run, the forwards function is executed. To do this:

.. code-block:: bash

    piccolo migrations forwards my_app

-------------------------------------------------------------------------------

Reversing migrations
--------------------

To reverse the migration, run this:

.. code-block:: bash

    piccolo migrations backwards 2018-09-04T19:44:09

You can try going forwards and backwards a few times to make sure it works as
expected.

-------------------------------------------------------------------------------

Checking migrations
-------------------

You can easily check which migrations have and haven't ran using the following:

.. code-block:: bash

    piccolo migrations check
