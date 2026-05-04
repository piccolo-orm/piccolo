Avoiding circular imports
=========================

How Python imports work
-----------------------

When Python imports a file, it evaluates it from top to bottom.

With :class:`ForeignKey  <piccolo.columns.column_types.ForeignKey>` columns we
sometimes have to reference tables lower down in the file (which haven't been
evaluated yet).

The solutions are:

* Try and move the referenced table to a different Python file.
* Use :class:`LazyTableReference <piccolo.columns.reference.LazyTableReference>`

Import ``Table`` definitions as early as possible
-------------------------------------------------

In the entrypoint to your app, at the top of the file, it's recommended to
import your tables.

.. code-block:: python

    # main.py
    from my_app.tables import Manager, Band

This ensures that the tables are imported, and setup correctly.

Keep table files focused
------------------------

You should try and keep your ``tables.py`` files pretty focused (i.e.
just contain your ``Table`` definitions).

If you have lots of logic alongside your ``Table`` definitions, it might cause
your ``LazyTableReference`` references to evaluate too soon (causing circular
import errors). An example of this is with
:func:`create_pydantic_model <piccolo.utils.pydantic.create_pydantic_model>`:

.. literalinclude:: avoiding_circular_imports_src/tables.py

Simplify your schema if possible
--------------------------------

Even with :class:`LazyTableReference <piccolo.columns.reference.LazyTableReference>`,
you may run into some problems if your schema is really complicated.

An example is when you have two tables, and they have foreign keys to each other.

.. code-block:: python

    class Band(Table):
        name = Varchar()
        manager = ForeignKey("Manager")


    class Manager(Table):
        name = Varchar()
        favourite_band = ForeignKey(Band)


Piccolo should be able to create these tables, and query them. However, some
Piccolo tooling may struggle - for example when loading :ref:`fixtures <Fixtures>`.

A joining table can help in these situations:

.. code-block:: python

    class Band(Table):
        name = Varchar()
        manager = ForeignKey("Manager")


    class Manager(Table):
        name = Varchar()


    class ManagerFavouriteBand(Table):
        manager = ForeignKey(Manager, unique=True)
        band = ForeignKey(Band)
