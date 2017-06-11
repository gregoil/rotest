#!/usr/bin/env python
import os
import sys
import django
from glob import glob
from os.path import pardir
from shutil import copy, Error


PY_FILES = '*.py'
# This var should contain all the apps that uses migration.
MIGRATIONS_PATHS = ('resources/migrations',
                    'rotest/core/migrations',
                    'rotest/management/migrations')


def copy_migrations():
    """Copy back migration files from obj to code directories.

    Raises:
        AssertionError: expected migration paths does not exist.
    """
    print 'Copying back migration files'
    code_path = os.path.abspath(os.path.join(__file__, pardir, pardir,
                                             pardir, pardir))
    obj_path = os.path.join(code_path, 'obj/host')

    # Check that the paths exists.
    assert os.path.isdir(code_path)
    assert os.path.isdir(obj_path)

    for migrations_dir in MIGRATIONS_PATHS:
        migrations_obj_dir = os.path.join(obj_path, migrations_dir)
        migrations_code_dir = os.path.join(code_path, migrations_dir)

        # Check that the paths exists.
        if (not os.path.isdir(migrations_obj_dir) or
            not os.path.isdir(migrations_code_dir)):
            continue

        # Copy all the generated migration code files.
        for path in glob(os.path.join(migrations_obj_dir, PY_FILES)):
            try:
                copy(path, migrations_code_dir)
                print 'Copied ' + path
            except Error:
                # This error is raised when the two files are identical.
                pass


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "all_settings")

    # Load django models. This is needed to populate the DB before using it.
    django.setup()

    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

    # TODO: Remove copy back migrations once issue QA-1176 is solved.
    if 'obj' not in os.path.abspath(__file__) and 'makemigrations' in sys.argv:
        copy_migrations()


if __name__ == "__main__":
    main()
