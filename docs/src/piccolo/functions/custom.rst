Custom functions
================

If there's a database function which Piccolo doesn't provide out of the box,
you can still easily access it by using :class:`QueryString <piccolo.querystring.QueryString>`
directly.

QueryString
-----------

:class:`QueryString <piccolo.querystring.QueryString>` is the building block of
queries in Piccolo.

If we have a custom function defined in the database called ``slugify``, you
can access it like this:

.. code-block:: python

    from piccolo.querystring import QueryString

    await Band.select(
        Band.name,
        QueryString('slugify({})', Band.name, alias='name_slug')
    )
