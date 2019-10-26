import click

from piccolo.commands.playground import playground
from piccolo.commands.migration.new import new
from piccolo.commands.migration.backwards import backwards
from piccolo.commands.migration.forwards import forwards


@click.group()
def cli():
    pass


@cli.group("migration")
def migration():
    pass


migration.add_command(new)
migration.add_command(forwards)
migration.add_command(backwards)

cli.add_command(playground)


def main():
    cli()


if __name__ == "__main__":
    main()
