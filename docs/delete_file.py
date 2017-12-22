"""Delete either a file of a directory with its contents.

Usage:
    delete_file.py <file>
"""
import os
import shutil

import docopt


if __name__ == "__main__":
    arguments = docopt.docopt(__doc__)
    target_file = arguments["<file>"]

    if os.path.isfile(target_file):
        os.remove(target_file)
    elif os.path.isdir(target_file):
        shutil.rmtree(target_file)
