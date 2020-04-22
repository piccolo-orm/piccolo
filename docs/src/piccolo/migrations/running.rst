Running migrations
==================

Forwards
--------

When the migration is run, the forwards function is executed. To do this:

.. code-block:: bash

    piccolo migrations forwards my_app

Reversing migrations
--------------------

To reverse the migration, run this:

.. code-block:: bash

    piccolo migrations backwards 2018-09-04T19:44:09

This executes the backwards function.

You can try going forwards and backwards a few times to make sure it works as
expected.

.. warning:: Auto migrations don't currently support going backwards.

Checking migrations
-------------------

You can easily check which migrations have amd haven't ran using the following:

.. code-block:: bash

    piccolo migrations check
