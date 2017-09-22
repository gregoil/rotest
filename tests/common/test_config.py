"""Testing configuration from CLI, env-vars and YAML files."""
import unittest
from collections import OrderedDict

import yaml
import mock
from rotest.common.config import Option, get_configuration, search_config_file


class CommandLineTest(unittest.TestCase):
    def test_command_line_option_with_space(self):
        """Test a command line option of the form '--option value'."""
        schema = {"target": Option(command_line_options=["--option"])}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py", "--option value"])

        self.assertEqual(configuration, {"target": "value"})

    def test_command_line_option_with_equation(self):
        """Test a command line option of the form '--option=value'."""
        schema = {"target": Option(command_line_options=["--option"])}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py", "--option=value"])

        self.assertEqual(configuration, {"target": "value"})

    def test_command_line_options_overriding(self):
        """Assert that the last used command line option takes predecense."""
        schema = {"target": Option(command_line_options=["--option1",
                                                         "--option2"])}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py", "--option1=value1",
                                  "--option2", "value2"])

        self.assertEqual(configuration, {"target": "value2"})


class EnvironmentVariableTest(unittest.TestCase):
    def test_environment_variables(self):
        """Test two targets derived from two different env-vars."""
        schema = {"target1": Option(environment_variables=["ENVIRON1"]),
                  "target2": Option(environment_variables=["ENVIRON2"])}

        configuration = get_configuration(
            configuration_schema=schema,
            environment_variables={"ENVIRON1": "value1",
                                   "ENVIRON2": "value2"})

        self.assertEqual(configuration, {"target1": "value1",
                                         "target2": "value2"})

    def test_command_line_prioritized_over_environment_variable(self):
        """Asert that a command line option takes predecense over env-var."""
        schema = {"target": Option(command_line_options=["option"],
                                   environment_variables=["ENVIRON"])}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py", "--option=value"],
            environment_variables={"ENVIRON": "value"})

        self.assertEqual(configuration, {"target": "value"})

    def test_first_environment_variable_wins(self):
        """Assert that the first defined source env-var takes predecense."""
        schema = {"target": Option(environment_variables=["ENVIRON1",
                                                          "ENVIRON2"])}

        configuration = get_configuration(
            configuration_schema=schema,
            environment_variables=OrderedDict([("ENVIRON2", "value2"),
                                               ("ENVIRON1", "value1")]))

        self.assertEqual(configuration, {"target": "value1"})


class ConfigFileTest(unittest.TestCase):
    def test_configuration_file(self):
        """Test target derived from the configuration file."""
        schema = {"target": Option(config_file_options=["option"])}

        configuration = get_configuration(
            configuration_schema=schema,
            config_content="rotest:\n  option: value")

        self.assertEqual(configuration, {"target": "value"})

    def test_environment_variable_prioritized_over_configuration_file(self):
        """Asert that an env-var takes predecense over configuration file."""
        schema = {"target": Option(environment_variables=["ENVIRON"],
                                   config_file_options=["option"])}

        configuration = get_configuration(
            configuration_schema=schema,
            environment_variables={"ENVIRON": "value1"},
            config_content="rotest:\n  option: value2")

        self.assertEqual(configuration, {"target": "value1"})

    def test_file_configuration_prioritized_over_default_value(self):
        """Assert that the config file takes predecense over default value."""
        schema = {"target": Option(config_file_options=["option"],
                                   default_value="default")}

        configuration = get_configuration(
            configuration_schema=schema,
            config_content="rotest:\n  option: value")

        self.assertEqual(configuration, {"target": "value"})

    def test_first_configuration_file_option_wins(self):
        """Assert the first option in the config file takes predecense."""
        schema = {"target": Option(config_file_options=["option1", "option2"])}
        config_content = "rotest:\n  option2: value2\n  option1: value1"

        configuration = get_configuration(
            configuration_schema=schema,
            config_content=config_content)

        self.assertEqual(configuration, {"target": "value1"})

    def test_configuration_parsing_error(self):
        """Assert error when the configuration file isn't in YAML format."""
        schema = {"target": Option()}

        with self.assertRaises(yaml.YAMLError):
            get_configuration(configuration_schema=schema,
                              config_content="][")

    def test_rotest_section_not_preset(self):
        """Assert not using the config file if there is no 'rotest' section."""
        schema = {"target": Option(config_file_options=["option"],
                                   default_value="default")}

        configuration = get_configuration(
            configuration_schema=schema,
            config_content="other:\n  key: value")

        self.assertEqual(configuration, {"target": "default"})

    @mock.patch("os.path.abspath",
                return_value="/home/user/project/")
    @mock.patch("os.path.isfile",
                side_effect=lambda path:
                            path == "/home/user/project/.rotest.yml")
    def test_finding_configuration_file_on_current_directory(self, *_args):
        """Test finding the config file in the direct ancestor."""
        self.assertEqual(search_config_file(),
                         "/home/user/project/.rotest.yml")

    @mock.patch("os.path.abspath",
                return_value="/home/user/project/sub1/sub2/")
    @mock.patch("os.path.isfile",
                side_effect=lambda path:
                            path == "/home/user/project/.rotest.yml")
    def test_finding_configuration_file_on_ancestor_directories(self, *_args):
        """Test finding the config file in the non-direct ancestor."""
        self.assertEqual(search_config_file(),
                         "/home/user/project/.rotest.yml")


class EdgeCaseTest(unittest.TestCase):
    def test_default_value(self):
        """Assert a default value is chosen if there is no other option."""
        schema = {"target": Option(default_value="value")}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py"])

        self.assertEqual(configuration, {"target": "value"})

    def test_no_value_given(self):
        """Assert that None is received if there is no default value."""
        schema = {"target": Option(command_line_options=["value"])}

        configuration = get_configuration(
            configuration_schema=schema,
            command_line_options=["script.py"])

        self.assertEqual(configuration, {"target": None})


if __name__ == "__main__":
    unittest.main()
