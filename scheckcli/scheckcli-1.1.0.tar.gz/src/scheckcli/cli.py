"""
Module that contains the command line app.

"""

from os import environ
import click
import yaml
from cerberus import Validator, SchemaError


class ProcessFiles:
    """Reads the input schema files

    Args:
        schema_file_path (filePath, required): file path to the schema file.
        input_file_path  (filePath, optional): file path to the schema file.
    Returns:

    """

    def __init__(self, schema_file_path, input_file_path=None):
        self.schema_file_path = schema_file_path
        self.input_file_path = input_file_path or {}
        self._get_input = None
        self._get_schema = None
        self.stream = None
        self.validate = None

    def get_yaml(self, file_path=None):
        """yaml.SafeLoads the file provided in file_path.

        Args:
            file_path (_type_, optional): _description_. Defaults to None.
        Raises:
            raises a yaml.YAMLError if the yaml syntax is invalid
        Returns:
            yaml Object:
        """
        with open(file_path, "r", encoding="utf-8") as self.stream:
            try:
                return yaml.load(self.stream, Loader=yaml.SafeLoader)
            except yaml.YAMLError as exception:
                return print(
                    "The file does not have a valid structure: ",
                    exception,
                )

    def get_schema(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        if self._get_schema is None:
            self._get_schema = self.get_yaml(
                file_path=self.schema_file_path
            )
            self.validate = Validator(self._get_schema)
            return self.validate
        try:
            return (self._get_schema, self.validate)
        except TypeError as exception:
            return print("Invalid Schema file Exception: ", exception)

    def get_input(self):
        '''loads the input file'''
        if self._get_input is None:
            self._get_input = self.get_yaml(
                file_path=self.input_file_path
            )

    def compare(self):
        """
        compare_cmd validates the input file
        has the same schema as the schema file.

        Args:
            schema_file_path (file_path): File path of the schema file.
            input_file_path (file_path): File path of the input file.
        """
        self.get_schema()
        self.get_input()
        try:
            if self.validate.validate(self._get_input):
                return print('Input file has a valid schema.'), 0
            raise Exception(self.validate.errors)
        except SchemaError as exception:
            raise exception


@click.group()
def cli1():
    """create cli click group"""
    pass  # pylint: disable=W0107


@cli1.command(
    'compare',
    no_args_is_help=True,
    short_help="Compare schema of the input file against a schema file.",
    help="""\b
    Compare schema of the input file against a schema file.
    
    EXAMPLES:

        scheckcli compare -sfp ./schema.yaml -ifp./input.yaml
    
        scheckcli compare -sfp ./schema.json -ifp ./input.json
    """,
)
@click.option(
    '--schema-file-path',
    '-sfp',
    required=True,
    help="""
        The file path to the schema file.
        Configurable with SCHECK_SCHEMA_PATH environmental Variable""",
    default=lambda: environ.get("SCHECK_SCHEMA_PATH"),
    type=click.Path(exists=True, file_okay=True),
)
@click.option(
    '--input-file-path',
    '-ifp',
    required=True,
    help="""
    The file path to the input file to compare.
    Configurable with SCHECK_INPUT_PATH environmental variable.""",
    default=lambda: environ.get("SCHECK_INPUT_PATH"),
    type=click.Path(exists=True, file_okay=True),
)
def compare_cmd(schema_file_path, input_file_path):
    """
    compare_cmd validates the input file
    has the same schema as the schema file.

    Args:
        schema_file_path (file_path): File path of the schema file.
        input_file_path (file_path): File path of the input file.
    """
    comp = ProcessFiles(schema_file_path, input_file_path)
    comp.compare()


@click.group()
def cli2():
    """create cli2 click group"""
    pass  # pylint: disable=W0107


@cli2.command(
    'check',
    no_args_is_help=True,
    short_help="Checks the provided schema file for valid syntax.",
    help="""\b
    Checks the provided schema file for valid syntax. Both json or yaml are accepted file types.
    
    EXAMPLES:
    
        scheckcli check ./schema.yaml

        scheckcli check ./schema.json

        scheckcli check --sfp ./schema.yaml

        scheckcli check --sfp ./schema.json
    """,
)
@click.option(
    '--schema-file-path',
    '-sfp',
    required=True,
    help="""
    The file path to the schema file.
    Configurable with SCHECK_SCHEMA_PATH environmental Variable""",
    default=lambda: environ.get("SCHECK_SCHEMA_PATH"),
    type=click.Path(exists=True, file_okay=True),
)
def check_command(schema_file_path):
    """check_command ensure schema file is valid.

    Args:
        schema_file_path (filePath): The file path of the schema file.
    """
    comp = ProcessFiles(schema_file_path)
    if comp.get_schema():
        print("The Schema file has valid syntax.")


main = click.CommandCollection(
    sources=[cli1, cli2],
    help="""
        Compare given input file with given schema file. Check's the provided schema file for valid schema syntax.
        """,
)
