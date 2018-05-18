#!/usr/bin/env python
import click
import django

from rotest.cli.server import server
from rotest.core.runner import main as run


@click.group(
    context_settings=dict(
        help_option_names=['-h', '--help'],
    )
)
@click.version_option()
def cli():
    pass


def main():
    """Run the main `rotest` program."""
    # Load django models before using the runner in tests.
    django.setup()

    cli.add_command(run, name="run")
    cli.add_command(server)
    cli()


if __name__ == "__main__":
    main()
