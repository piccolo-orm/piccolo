import click

from tests.postgres_container import TestPostgres


@click.command()
@click.option("--db_engine", help="One of: postgres|sqlite")
@click.option("--action", help="One of: spin_up|tear_down")
def setup(db_engine: str, action: str):
    if db_engine == "postgres":
        postgres = TestPostgres()
        do = getattr(postgres, action)
        do()
    else:
        return NotImplementedError


if __name__ == "__main__":
    setup()
