Installing Piccolo
==================

Python
------

You need `Python 3.7 <https://www.python.org/downloads/>`_ or above installed on your system.

-------------------------------------------------------------------------------

Pip
---

Now install piccolo, ideally inside a `virtualenv <https://docs.python-guide.org/dev/virtualenvs/>`_:

.. code-block:: python

    # Optional - creating a virtualenv on Unix:
    python3 -m venv my_project
    cd my_project
    source bin/activate

    # The important bit:
    pip install piccolo

    # Install Piccolo with PostgreSQL driver:
    pip install 'piccolo[postgres]'

    # Install Piccolo with SQLite driver:
    pip install 'piccolo[sqlite]'

    # Optional: orjson for improved JSON serialisation performance
    pip install 'piccolo[orjson]'

    # Optional: uvloop as the default event loop instead of asyncio
    # If using Piccolo with Uvicorn, Uvicorn will set uvloop as the default
    # event loop if installed
    pip install 'piccolo[uvloop]'

    # If you just want Piccolo with all of it's functionality, you might prefer
    # to use this:
    pip install 'piccolo[all]'
