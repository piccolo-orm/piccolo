Serialization
=============

``Piccolo`` uses `Pydantic <https://github.com/samuelcolvin/pydantic>`_
internally to serialize and deserialize data.

create_pydantic_model
---------------------

Using ``create_pydantic_model`` we can easily create a `Pydantic model <https://pydantic-docs.helpmanual.io/usage/models/>`_
from a Piccolo ``Table``. With ``create_pydantic_model`` you have several options depending on how you want to display the data.

For example, if we want to exclude column ``bio`` from BandModel:

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Text, Varchar

    class Manager(Table):
        name = Varchar()

    class Band(Table):
        name = Varchar(length=100)
        bio = Text()
        manager = ForeignKey(Manager)

    BandModel = create_pydantic_model(Band, exclude_columns=(Band.bio,))

Another great feature is ``nested=True``. With that feature
for each ``ForeignKey`` in the Piccolo table, the Pydantic model will contain a 
sub model for the related table.

For example:

.. code-block:: python

    from piccolo.table import Table
    from piccolo.columns import ForeignKey, Varchar

    class Manager(Table):
        name = Varchar()

    class Band(Table):
        name = Varchar()
        manager = ForeignKey(Manager)

    BandModel = create_pydantic_model(Band, nested=True)

If we were to write ``BandModel`` by hand instead, it would look like this:

.. code-block:: python

    from pydantic import BaseModel

    class ManagerModel(BaseModel):
        name: str

    class BandModel(BaseModel):
        name: str
        manager: ManagerModel

but with ``nested=True`` we can achieve this with one line of code.

Best place to look ``create_pydantic_model`` in action is 
`PiccoloCRUD <https://github.com/piccolo-orm/piccolo_api/blob/master/piccolo_api/crud/endpoints.py>`_
because ``PiccoloCRUD`` internally use ``create_pydantic_model`` to create a 
Pydantic model from a Piccolo table.

Source
~~~~~~

.. automodule:: piccolo.utils.pydantic
    :members:

FastAPI template
~~~~~~~~~~~~~~~~

To create a new FastAPI app using Piccolo, simply use:

.. code-block:: bash

    piccolo asgi new

This uses ``create_pydantic_model`` to create serializers.

See the `Piccolo ASGI docs <https://piccolo-orm.readthedocs.io/en/latest/piccolo/asgi/index.html>`_
for details.
