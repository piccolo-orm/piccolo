import click

from piccolo.commands.playground import playground
from piccolo.commands.migration.new import new
from piccolo.commands.migration.backwards import backwards
from piccolo.commands.migration.forwards import forwards


@click.group("migration")
def cli():
    pass


cli.add_command(new)
cli.add_command(forwards)
cli.add_command(backwards)
cli.add_command(playground)


def main():
    cli()


if __name__ == "__main__":
    main()
