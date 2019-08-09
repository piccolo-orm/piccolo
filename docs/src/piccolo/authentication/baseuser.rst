.. _BaseUser:

BaseUser
========

Inherit from ``BaseUser`` to create your own User table.

.. code-block:: python

    from piccolo.extensions.user import BaseUser


    class User(BaseUser):

        class Meta():
            tablename = 'custom_user'

.. hint:: A table name of `user` isn't allowed since it clashes with a keyword in Postgres - so override the ``tablename`` in ``Meta``, if you choose to name your class ``User``.
