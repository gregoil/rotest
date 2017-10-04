"""Json parser and validator."""
# pylint: disable=multiple-statements
import json

from attrdict import AttrDict
from jsonschema import validate


def parse(json_path, schema_path=None):
    """Parse the Json file into attribute dictionary.

    Args:
        json_path (str): path of the Json file.
        schema_path (str): path of the schema file - optional.

    Returns:
        AttrDict. representing the Json file .

    Raises:
        jsonschema.ValidationError: Json file does not comply with the schema.
    """
    with open(json_path) as config_file:
        json_content = json.load(config_file)

    if schema_path is not None:

        with open(schema_path) as schema:
            schema_content = json.load(schema)

        validate(json_content, schema_content)

    return AttrDict(json_content)
