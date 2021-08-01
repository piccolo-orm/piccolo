Installing Piccolo
==================

Python
------

You need `Python 3.7 <https://www.python.org/downloads/>`_ or above installed on your system.

Pip
---

Now install piccolo, ideally inside a `virtualenv <https://docs.python-guide.org/dev/virtualenvs/>`_:

.. code-block:: python

    # Optional - creating a virtualenv on Unix:
    python3.7 -m venv my_project
    cd my_project
    source bin/activate

    # The important bit:
    pip install piccolo

    # Optional: orjson for improved JSON serialisation performance
    pip install piccolo[orjson]

    # Optional: uvloop as default event loop instead of asyncio
    # If using Piccolo with Uvicorn, Uvicorn will set uvloop as
    # default event loop if installed
    pip install piccolo[uvloop]
