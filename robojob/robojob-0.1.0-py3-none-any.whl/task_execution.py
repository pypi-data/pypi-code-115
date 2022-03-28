import inspect
import re
import subprocess

class TaskException(Exception): pass

class TaskExecution:
    def __init__(self, name):
        self.name = name
        self.parameters = dict()
        self.id = None
        self.status = "Started"
        self.error_message = ""
    
    def bind_parameters(self, context_parameters):
        raise NotImplementedError()

    def execute(self):
        raise NotImplementedError()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name}>"


class FunctionExecution(TaskExecution):
    def __init__(self, func):
        super().__init__(name=func.__name__)
        self.func = func

    def bind_parameters(self, context_parameters):
        for name in inspect.signature(self.func).parameters.keys():
            self.parameters[name] = context_parameters.get(name)

    def execute(self):
        self.func(**self.parameters)
        

class StoredProcedureExecution(TaskExecution):
    def __init__(self, connection, schema_name, procedure_name):
        super().__init__(name=f"{schema_name}.{procedure_name}")
        self.connection = connection
        self.schema_name = schema_name
        self.procedure_name = procedure_name

    def bind_parameters(self, context_parameters):
        for (name,) in self.connection.execute(
                """
                SELECT PARAMETER_NAME
                FROM INFORMATION_SCHEMA.PARAMETERS
                WHERE SPECIFIC_SCHEMA = ? AND SPECIFIC_NAME = ?
                ORDER BY ORDINAL_POSITION
                """, self.schema_name, self.procedure_name):
            self.parameters[name] = context_parameters.get(name)

    def execute(self):
        parameter_names = list()
        parameter_values = list()
        for name, value in self.parameters.items():
            parameter_names.append(name)
            parameter_values.append(value)
        sql_parameter_list = ", ".join(f"{key} = ?" for key in parameter_names)
        execute_query = f"EXEC [{self.schema_name}].[{self.procedure_name}] {sql_parameter_list}"
        cursor = self.connection.cursor()
        cursor.execute(execute_query, parameter_values)


class RExecution(TaskExecution):
    def __init__(self, filename):
        super().__init__(name=filename)
        self.filename = filename
        self.parameter_names = list()

    def bind_parameters(self, context_parameters):
        with open(self.filename, 'r') as scriptfile:
            first_line = scriptfile.readline()
        if not first_line.strip():
            return
        self.parameter_names = re.findall("[a-z_0-9]+", first_line, re.IGNORECASE)
        for parameter_name in self.parameter_names:
            self.parameters[parameter_name] = context_parameters[parameter_name]

    def execute(self):
        parameter_values = list()
        for name in self.parameter_names:
            value = self.parameters.get(name)
            if value is None:
                parameter_values.append('""')
            else:
                parameter_values.append(f'"{str(value)}"')
        result = subprocess.run(["RScript.exe", "--encoding=utf8", self.filename] + parameter_values, capture_output=True)
        if result.returncode != 0:
            raise TaskException(result.stderr)


class PowershellExecution(TaskExecution):
    def __init__(self, filename):
        super().__init__(name=filename)
        self.filename = filename
        self.parameter_names = list()

    def bind_parameters(self, context_parameters):
        with open(self.filename, 'r') as scriptfile:
            parameter_declaration = scriptfile.readline()
        m = re.match("param\(([^)]*)\)", parameter_declaration, flags=re.IGNORECASE)
        if m:
            param_string = m.group(1)
            self.parameter_names = [arg.strip() for arg in param_string.split(",")]
            for parameter_name in self.parameter_names:
                self.parameters[parameter_name] = context_parameters[parameter_name]

    def execute(self):
        parameter_values = list()
        for name in self.parameter_names:
            value = self.parameters.get(name)
            if value is None:
                parameter_values.append('""')
            else:
                parameter_values.append(f'"{str(value)}"')
        result = subprocess.run(["powershell", "-File", self.filename] + parameter_values, capture_output=True)
        if result.stderr:
            raise TaskExecution(result.stderr)
