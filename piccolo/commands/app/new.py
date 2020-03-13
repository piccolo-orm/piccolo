from __future__ import annotations

import click


@click.argument("app_name")
@click.command()
def new(app_name: str):
    """
    Creates a new Piccolo app.
    """
    print(f"Creating {app_name} app ...")
