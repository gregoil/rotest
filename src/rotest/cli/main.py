#!/usr/bin/env python
from __future__ import absolute_import
import sys

import django
django.setup()

from rotest.cli.client import main as run  # noqa
from rotest.cli.server import start_server  # noqa
from rotest.management.utils.shell import main as shell  # noqa


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        shell()

    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()

    else:
        run()
