Serialization
=============

Piccolo uses `Pydantic <https://github.com/samuelcolvin/pydantic>`_ internally
to serialize and deserialize data.

-------------------------------------------------------------------------------

create_pydantic_model
---------------------

Using ``create_pydantic_model`` we can easily create a `Pydantic model <https://pydantic-docs.helpmanual.io/usage/models/>`_
from a Piccolo ``Table``.

Using this example schema:

.. code-block:: python

    from piccolo.columns import ForeignKey, Integer, Varchar
    from piccolo.table import Table

    class Manager(Table):
        name = Varchar()

    class Band(Table):
        name = Varchar(length=100)
        manager = ForeignKey(Manager)
        popularity = Integer()

Creating a Pydantic model is as simple as:

.. code-block:: python

    from piccolo.utils.pydantic import create_pydantic_model

    BandModel = create_pydantic_model(Band)

We can then create model instances from data we fetch from the database:

.. code-block:: python

    # If using objects:
    model = BandModel(
        **Band.objects().get(Band.name == 'Pythonistas').run_sync().to_dict()
    )

    # If using select:
    model = BandModel(
        **Band.select().where(Band.name == 'Pythonistas').first().run_sync()
    )

    >>> model.name
    'Pythonistas'

You have several options for configuring the model, as shown below.

include_columns / exclude_columns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If we want to exclude the ``popularity`` column from the ``Band`` table:

.. code-block:: python

    BandModel = create_pydantic_model(Band, exclude_columns=(Band.popularity,))

Conversely, if you only wanted the ``popularity`` column:

.. code-block:: python

    BandModel = create_pydantic_model(Band, include_columns=(Band.popularity,))

nested
~~~~~~

Another great feature is ``nested=True``. For each ``ForeignKey`` in the
Piccolo ``Table``, the Pydantic model will contain a sub model for the related
table.

For example:

.. code-block:: python

    BandModel = create_pydantic_model(Band, nested=True)

If we were to write ``BandModel`` by hand instead, it would look like this:

.. code-block:: python

    from pydantic import BaseModel

    class ManagerModel(BaseModel):
        name: str

    class BandModel(BaseModel):
        name: str
        manager: ManagerModel
        popularity: int

But with ``nested=True`` we can achieve this with one line of code.

To populate a nested Pydantic model with data from the database:

.. code-block:: python

    # If using objects:
    model = BandModel(
        **Band.objects(Band.manager).get(Band.name == 'Pythonistas').run_sync().to_dict()
    )

    # If using select:
    model = BandModel(
        **Band.select(
            Band.all_columns(),
            Band.manager.all_columns()
        ).where(
            Band.name == 'Pythonistas'
        ).first().output(
            nested=True
        ).run_sync()
    )

    >>> model.manager.name
    'Guido'

include_default_columns
~~~~~~~~~~~~~~~~~~~~~~~

Sometimes you'll want to include the Piccolo ``Table``'s primary key column in
the generated Pydantic model. For example, in a ``GET`` endpoint, we usually
want to include the ``id`` in the response:

.. code-block:: javascript

    // GET /api/bands/1/
    // Response:
    {"id": 1, "name": "Pythonistas", "popularity": 1000}

Other times, you won't want the Pydantic model to include the primary key
column. For example, in a ``POST`` endpoint, when using a Pydantic model to
serialise the payload, we don't expect the user to pass in an ``id`` value:

.. code-block:: javascript

    // POST /api/bands/
    // Payload:
    {"name": "Pythonistas", "popularity": 1000}

By default the primary key column isn't included - you can add it using:

.. code-block:: python

    BandModel = create_pydantic_model(Band, include_default_columns=True)

Source
~~~~~~

.. currentmodule:: piccolo.utils.pydantic

.. autofunction:: create_pydantic_model

.. hint:: A good place to see ``create_pydantic_model`` in action is `PiccoloCRUD <https://github.com/piccolo-orm/piccolo_api/blob/master/piccolo_api/crud/endpoints.py>`_,
  as it uses ``create_pydantic_model`` extensively to create Pydantic models
  from Piccolo tables.

-------------------------------------------------------------------------------

FastAPI template
----------------

Piccolo's FastAPI template uses ``create_pydantic_model`` to create serializers.

To create a new FastAPI app using Piccolo, simply use:

.. code-block:: bash

    piccolo asgi new

See the :ref:`ASGI docs <ASGICommand>` for more details.
