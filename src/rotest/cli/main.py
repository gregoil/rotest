#!/usr/bin/env python
import click
import django

from rotest.cli.server import server
from rotest.cli.client import main as run


@click.group(
    context_settings=dict(
        help_option_names=['-h', '--help'],
    )
)
@click.version_option()
def main():
    # Load django models before using the runner in tests.
    django.setup()


main.add_command(run, name="run")
main.add_command(server)
