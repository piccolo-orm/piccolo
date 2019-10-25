import click

from piccolo.commands.playground import playground
from piccolo.commands.migration import new, forwards, backwards


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
