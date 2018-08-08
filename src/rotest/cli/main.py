#!/usr/bin/env python
import sys

from rotest.cli.server import server
from rotest.cli.client import main as run
from rotest.management.utils.shell import main as shell


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server()
    elif len(sys.argv) > 1 and sys.argv[1] == "shell":
        shell()
    else:
        run()
