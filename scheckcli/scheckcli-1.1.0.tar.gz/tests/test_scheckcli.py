# pylint: disable-all
"""Test file for cli.py
"""
from unittest import TestCase
import cerberus
from click.testing import CliRunner
from scheckcli.cli import main


class SetUp:
    """SetUp class for the  creates the click runner and reusuable data"""

    def click_runner(self, *args):
        """Creates a clirunner."""
        if args:
            self.runner = CliRunner()
            self.result = self.runner.invoke(main, args)
        else:
            self.runner = CliRunner()
            self.result = self.runner.invoke(main)
        return (self.runner, self.result)

    def click_runner_isolated_fs(self, *args):
        self.runner = CliRunner()
        with self.runner.isolated_filesystem():
            with open('schema.yaml', 'w') as sfp:
                sfp.write(self.load_schema_text)
            with open('input.yaml', 'w') as ifp:
                ifp.write(self.load_input_text)
            self.result = self.runner.invoke(main, args)
            return (self.result, sfp, ifp)

    def compare_click_runner_isolate_fs(self):
        SetUp.click_runner_isolated_fs(
            self, "compare", "-sfp", "schema.yaml", "-ifp", "input.yaml"
        )

    def check_click_runner_isolate_fs(self):
        SetUp.click_runner_isolated_fs(
            self, "check", "-sfp", "schema.yaml"
        )

    def base_assert(self):
        assert self.result.exit_code == 0
        assert "--help" in self.result.output
        assert "Show this message and exit." in self.result.output

    def valid_data(self):
        self.load_schema_text = """
            spec:
              type: dict
              required: true
              schema:
                name:
                  type: string
                  required: true
                feeds:
                  type: list
                  required: true
                  schema:
                    type: dict
                    schema:
                      name:
                        type: string
                        required: true
                      feedID:
                        type: string
                        required: true
        """
        self.load_input_text = """
            spec:
              name: testName
              feeds:
                - name: foo
                  feedID: bar
                - name: spam
                  feedID: eggs
        """
        return (self.load_schema_text, self.load_input_text)

    def invalid_data(self):
        self.load_schema_text = """
            spec:
        """
        self.load_input_text = """
            name:
        """
        return (self.load_schema_text, self.load_input_text)


class test_base(TestCase):
    def test_no_params(self):
        SetUp.click_runner(self)
        SetUp.base_assert(self)

    def test_compare_no_params(self):
        SetUp.click_runner(self, "compare")
        SetUp.base_assert(self)

    def test_check_no_params(self):
        SetUp.click_runner(self, "check")
        SetUp.base_assert(self)


class test_compare(TestCase):
    def test_no_ifp(self):
        SetUp.click_runner(
            self, "compare", "--schema-file-path", "schema.yaml"
        )
        assert self.result.exit_code == 2
        assert (
            "Error: Missing option '--input-file-path' / '-ifp'."
            in self.result.output
        )

    def test_no_sfp_input(self):
        SetUp.click_runner(self, "compare", "-ifp", "input.yaml")
        assert self.result.exit_code == 2
        assert (
            "Error: Missing option '--schema-file-path' / '-sfp'."
            in self.result.output
        )

    def test_missing_file(self):
        SetUp.click_runner(
            self, "compare", "-sfp", "schema.null", "-ifp", "input.null"
        )
        assert self.result.exit_code == 2
        assert (
            "Path 'schema.null' does not exist." in self.result.output
        )

    def test_schemafile_yaml_error(self):
        SetUp.valid_data(self)[1]
        SetUp.invalid_data(self)[0]
        SetUp.compare_click_runner_isolate_fs(self)
        assert self.result.exit_code == 1
        assert isinstance(self.result.exception, TypeError)

    def test_input_with_invalid_schema(self):
        SetUp.valid_data(self)[0]
        self.load_input_text = """
          name:
        """
        SetUp.compare_click_runner_isolate_fs(self)
        assert self.result.exit_code == 1
        assert isinstance(self.result.exception, Exception)

    def test_valid_schema_pass(self):
        SetUp.valid_data(self)
        SetUp.compare_click_runner_isolate_fs(self)
        assert self.result.exit_code == 0
        assert 'Input file has a valid schema.' in self.result.output

    def test_empty_schema_pass(self):
        SetUp.valid_data(self)[1]
        self.load_schema_text = """"""
        SetUp.compare_click_runner_isolate_fs(self)
        assert self.result.exit_code == 1
        assert isinstance(self.result.exception, cerberus.SchemaError)


class test_check(TestCase):
    def test_valid_schema(self):
        SetUp.valid_data(self)[0]
        SetUp.check_click_runner_isolate_fs(self)
        assert self.result.exit_code == 0
        assert 'The Schema file has valid syntax.' in self.result.output

    def test_invalid_schema(self):
        SetUp.invalid_data(self)[1]
        SetUp.check_click_runner_isolate_fs(self)
