=======
Indexes
=======

Single column index
===================

Index can be added to a single column using the ``index=True``
argument of ``Column``:

.. code-block:: python

    class Band(Table):
        name = Varchar(index=True)

Multi-column (composite) index
==============================

To manually create and drop multi-column indexes, we can use Piccolo's 
built-in methods ``create_index`` and ``drop_index``.

If you are using automatic migrations, we can specify the ``CompositeIndex``
argument and they handle the creation and deletion of these composite indexes. 

.. currentmodule:: piccolo.composite_index

.. autoclass:: CompositeIndex