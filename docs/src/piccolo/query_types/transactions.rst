.. _Transactions:

Transactions
============

Transactions allow multiple queries to be committed only once successful.

This is useful for things like migrations, where you can't have it fail in an
inbetween state.

Usage
-----

.. code-block:: python

    transaction = Band._meta.db.transaction()
    transaction.add(Manager.create_table())
    transaction.add(Concert.create_table())
    await transaction.run()
