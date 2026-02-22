API reference
=============

Table
-----

.. currentmodule:: piccolo.table

.. autoclass:: Table
    :members:

-------------------------------------------------------------------------------

SchemaManager
-------------

.. currentmodule:: piccolo.schema

.. autoclass:: SchemaManager
    :members:

-------------------------------------------------------------------------------

Column
------

.. currentmodule:: piccolo.columns.base

.. autoclass:: Column
    :members:


.. autoclass:: ColumnKwargs
    :members:
    :undoc-members:

-------------------------------------------------------------------------------

Aggregate functions
-------------------

Count
~~~~~

.. currentmodule:: piccolo.query.methods.select

.. autoclass:: Count

-------------------------------------------------------------------------------

Refresh
-------

.. currentmodule:: piccolo.query.methods.refresh

.. autoclass:: Refresh
    :members:

-------------------------------------------------------------------------------

LazyTableReference
------------------

.. currentmodule:: piccolo.columns

.. autoclass:: LazyTableReference
    :members:

-------------------------------------------------------------------------------

Enums
-----

Foreign Keys
~~~~~~~~~~~~

.. currentmodule:: piccolo.columns

.. autoclass:: OnDelete
    :members:
    :undoc-members:

.. autoclass:: OnUpdate
    :members:
    :undoc-members:

.. currentmodule:: piccolo.columns.indexes

Indexes
~~~~~~~

.. autoclass:: IndexMethod
    :members:
    :undoc-members:

-------------------------------------------------------------------------------

Column defaults
---------------

.. currentmodule:: piccolo.columns.defaults

Date
~~~~

.. autoclass:: DateOffset
    :members:


UUID
~~~~

.. autoclass:: UUID4
    :members:

-------------------------------------------------------------------------------

Testing
-------

.. currentmodule:: piccolo.testing.model_builder

ModelBuilder
~~~~~~~~~~~~

.. autoclass:: ModelBuilder
    :members:

.. currentmodule:: piccolo.table

create_db_tables / drop_db_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autofunction:: create_db_tables
.. autofunction:: create_db_tables_sync
.. autofunction:: drop_db_tables
.. autofunction:: drop_db_tables_sync

-------------------------------------------------------------------------------

QueryString
-----------

.. currentmodule:: piccolo.querystring

.. autoclass:: QueryString
