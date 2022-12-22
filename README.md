![Logo](https://raw.githubusercontent.com/piccolo-orm/piccolo/master/docs/logo_hero.png "Piccolo Logo")

![Tests](https://github.com/piccolo-orm/piccolo/actions/workflows/tests.yaml/badge.svg)
![Release](https://github.com/piccolo-orm/piccolo/actions/workflows/release.yaml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/piccolo-orm/badge/?version=latest)](https://piccolo-orm.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/piccolo?color=%2334D058&label=pypi)](https://pypi.org/project/piccolo/)
[![codecov](https://codecov.io/gh/piccolo-orm/piccolo/branch/master/graph/badge.svg?token=V19CWH7MXX)](https://codecov.io/gh/piccolo-orm/piccolo)

Piccolo is a fast, user friendly ORM and query builder which supports asyncio. [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/).

## Features

Some of it’s stand out features are:

- Support for sync and async.
- A builtin playground, which makes learning a breeze.
- Tab completion support - works great with iPython and VSCode.
- Batteries included - a User model, authentication, migrations, an [admin GUI](https://github.com/piccolo-orm/piccolo_admin), and more.
- Modern Python - fully type annotated.
- Make your codebase modular and scalable with Piccolo apps (similar to Django apps).

## Syntax

The syntax is clean and expressive.

You can use it as a query builder:

```python
# Select:
await Band.select(
    Band.name
).where(
    Band.popularity > 100
)

# Join:
await Band.select(
    Band.name,
    Band.manager.name
)

# Delete:
await Band.delete().where(
    Band.popularity < 1000
)

# Update:
await Band.update({Band.popularity: 10000}).where(
    Band.name == 'Pythonistas'
)
```

Or like a typical ORM:

```python
# To create a new object:
b = Band(name='C-Sharps', popularity=100)
await b.save()

# To fetch an object from the database, and update it:
b = await Band.objects().get(Band.name == 'Pythonistas')
b.popularity = 10000
await b.save()

# To delete:
await b.remove()
```

## Installation

Installing with PostgreSQL driver:

```bash
pip install 'piccolo[postgres]'
```

Installing with SQLite driver:

```bash
pip install 'piccolo[sqlite]'
```

Installing with all optional dependencies (easiest):

```bash
pip install 'piccolo[all]'
```

## Building a web app?

Let Piccolo scaffold you an ASGI web app, using Piccolo as the ORM:

```bash
piccolo asgi new
```

[Starlette](https://www.starlette.io/), [FastAPI](https://fastapi.tiangolo.com/), [BlackSheep](https://www.neoteroi.dev/blacksheep/), [Xpresso](https://xpresso-api.dev/) and [Starlite](https://starlite-api.github.io/starlite/) are currently supported.

## Are you a Django user?

We have a handy page which shows the equivalent of [common Django queries in Piccolo](https://piccolo-orm.readthedocs.io/en/latest/piccolo/query_types/django_comparison.html).

## Documentation

Our documentation is on [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/piccolo/getting_started/index.html).

We also have some great [tutorial videos on YouTube](https://www.youtube.com/channel/UCE7x5nm1Iy9KDfXPNrNQ5lA).
