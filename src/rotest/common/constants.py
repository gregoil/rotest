"""This file contains constants for rotest."""
import os

from attrdict import AttrDict

from .utils import parse_config_file

BOLD = 'bold'
DARK = 'dark'
UNDERLINE = 'underline'

RED = 'red'
BLUE = 'blue'
CYAN = 'cyan'
GREY = 'grey'
WHITE = 'white'
GREEN = 'green'
YELLOW = 'yellow'
MAGENTA = 'magenta'

FILE_FOLDER = os.path.dirname(__file__)
DEFAULT_SCHEMA_PATH = os.path.join(FILE_FOLDER, "schema.json")
DEFAULT_CONFIG_PATH = os.path.join(FILE_FOLDER, "default_config.json")
default_config = AttrDict(parse_config_file(DEFAULT_CONFIG_PATH,
                                            DEFAULT_SCHEMA_PATH))
