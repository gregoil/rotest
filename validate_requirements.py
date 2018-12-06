"""Assert requirements.txt file and actual installed dependencies match.

* Use the ``pip freeze`` command to determine what are the installed libraries,
  and find differences from the written requirements.
* At the end, write the actual dependencies to the file.
"""
from subprocess import check_call, check_output

GET_DEPENDENCIES_COMMAND = ["pip", "freeze", "--exclude-editable"]


def main():
    with open("requirements.txt", "rt") as requirements_file:
        written_requirements = dict(
            line.split("==")
            for line in requirements_file.read().split())

    actual_requirements = dict(
        line.split("==")
        for line in check_output(
            GET_DEPENDENCIES_COMMAND).decode("utf-8").split())

    try:
        diff = "Difference: {}".format(
            ", ".join(set(actual_requirements) ^ set(written_requirements)))
        assert actual_requirements == written_requirements, diff

    finally:
        with open("requirements.txt", "wt") as requirements_file:
            check_call(GET_DEPENDENCIES_COMMAND, stdout=requirements_file)


if __name__ == "__main__":
    main()
