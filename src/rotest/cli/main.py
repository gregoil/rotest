#!/usr/bin/env python
from __future__ import absolute_import
import sys

from rotest.cli.client import main as run
from rotest.cli.server import start_server
from rotest.management.utils.shell import main as shell


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "shell":
        shell()

    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        start_server()

    else:
        run()
