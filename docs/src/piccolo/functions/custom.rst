Custom functions
================

If there's a function which Piccolo doesn't provide out of the box, it's
really easy to add your own.

QueryString
-----------

``QueryString`` is the building block of queries in Piccolo.

If we have a custom function called ``slugify``, you can use it like this:

.. code-block:: python

    from piccolo.querystring import QueryString

    await Article.update({
        Article.slug: QueryString('slugify({})', Article.name),
        force=True
    })
