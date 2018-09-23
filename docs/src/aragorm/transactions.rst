============
Transactions
============

Transactions allow multiple queries to be comitted only once successful.

This is useful for things like migrations, where you can't have it fail in an inbetween state.

Usage
=====

.. code::python
    transaction = Pokemon.Meta.db.transaction()
    transaction.add(Trainer.create())
    transaction.add(Match.create())
    await transaction.run()
