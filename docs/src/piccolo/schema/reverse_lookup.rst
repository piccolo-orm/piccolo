.. currentmodule:: piccolo.columns.reverse_lookup

##############
Reverse Lookup
##############

For example, we might have our ``Manager`` table, and we want to 
get all the bands associated with the same manager. 
For this we can use reverse foreign key lookup.

We create it in Piccolo like this:

.. code-block:: python

    from piccolo.columns.column_types import (
        ForeignKey,
        LazyTableReference,
        Varchar
    )
    from piccolo.columns.reverse_lookup import ReverseLookup
    from piccolo.table import Table


    class Manager(Table):
        name = Varchar()
        bands = ReverseLookup(
            LazyTableReference("Band", module_path=__name__),
            reverse_fk="manager",
        )


    class Band(Table):
        name = Varchar()
        manager = ForeignKey(Manager)

-------------------------------------------------------------------------------

Select queries
==============

If we want to select each manager, along with a list of associated band names,
we can do this:

.. code-block:: python

    >>> await Manager.select(Manager.name, Manager.bands(Band.name, as_list=True))
    [
        {'name': 'John', 'bands': ['C-Sharps']},
        {'name': 'Guido', 'bands': ['Pythonistas', 'Rustaceans']},
    ]

You can request whichever column you like from the reverse lookup:

.. code-block:: python

    >>> await Manager.select(Manager.name, Manager.bands(Band.id, as_list=True))
    [
        {'name': 'John', 'bands': [3]}, 
        {'name': 'Guido', 'bands': [1, 2]},
    ]

You can also request multiple columns from the reverse lookup:

.. code-block:: python

    >>> await Manager.select(Manager.name, Manager.bands(Band.id, Band.name))
    [
        {
            'name': 'John',
            'bands': [
                {'id': 3, 'name': 'C-Sharps'},
            ]
        },
        {   
            'name': 'Guido', 
            'bands': [
                {'id': 1, 'name': 'Pythonistas'}, 
                {'id': 2, 'name': 'Rustaceans'},
            ]
        }
    ]

If you omit the columns argument, then all of the columns are returned.

.. code-block:: python

    >>> await Manager.select(Manager.name, Manager.bands())
    [
        {
            'name': 'John',
            'bands': [
                {'id': 3, 'name': 'C-Sharps'},
            ]
        },
        {   
            'name': 'Guido', 
            'bands': [
                {'id': 1, 'name': 'Pythonistas'}, 
                {'id': 2, 'name': 'Rustaceans'},
            ]
        }
    ]

The default order of reverse lookup results is ascending, but if you 
specify ``descending=True``, you can get the results in descending order.

.. code-block:: python

    >>> await Manager.select(Manager.name, Manager.bands(descending=True))
    [
        {
            'name': 'John',
            'bands': [
                {'id': 3, 'name': 'C-Sharps'},
            ]
        },
        {   
            'name': 'Guido', 
            'bands': [
                {'id': 2, 'name': 'Rustaceans'},
                {'id': 1, 'name': 'Pythonistas'}, 
            ]
        }
    ]

Object queries
==============

We can also use object queries to ``ReverseLookup``.

get_reverse_lookup
------------------

.. currentmodule:: piccolo.table

.. automethod:: Table.get_reverse_lookup
    :noindex:
