.. _Create:

Create Table
============

This creates the table and columns in the database.

.. hint:: You can use migrations instead of manually altering the schema - see :ref:`Migrations`.

.. code-block:: python

    >>> Band.create_table().run_sync()
    []


To prevent an error from being raised if the table already exists:

.. code-block:: python

    >>> Band.create_table(if_not_exists=True).run_sync()
    []

Also, you can create multiple tables at once.

This function will automatically sort tables based on their foreign keys so they're created in the right order:

.. code-block:: python
    
    >>> from piccolo.table import create_tables 
    >>> create_tables(Band, Manager, if_not_exists=True)
   
