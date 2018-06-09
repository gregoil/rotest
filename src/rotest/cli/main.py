#!/usr/bin/env python
import sys

from rotest.cli.server import server
from rotest.cli.client import main as run


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        server()
    else:
        run()
