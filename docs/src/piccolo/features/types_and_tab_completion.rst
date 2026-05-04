..  _tab_completion:

Types and Tab Completion
========================

Type annotations
----------------

The Piccolo codebase uses type annotations extensively. This means it has great
tab completion support in tools like iPython and VSCode.

It also means it works well with type checkers like Mypy.

To learn more about how Piccolo achieves this, read this `article about type annotations <https://piccolo-orm.com/blog/improving-tab-completion-in-python-libraries>`_,
and this `article about descriptors <https://piccolo-orm.com/blog/the-power-of-python-descriptors/>`_.

-------------------------------------------------------------------------------

Troubleshooting
---------------

Here are some issues you may encounter when using Mypy, or another type
checker.

``id`` column doesn't exist
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you don't explicitly declare a column on your table with ``primary_key=True``,
Piccolo creates a ``Serial`` column for you called ``id``.

In the following situation, the type checker might complains that ``id``
doesn't exist:

.. code-block:: python

    await Band.select(Band.id)

You can fix this as follows:

.. code-block:: python

    # tables.py
    from piccolo.table import Table
    from piccolo.columns.column_types import Serial, Varchar


    class Band(Table):
        id: Serial  # Add an annotation
        name = Varchar()
