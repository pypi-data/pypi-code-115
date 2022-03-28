import os
import socket
import traceback
from typing import Any, Dict

from robojob.backends import LoggingBackend

from .task_execution import FunctionExecution, PowershellExecution, RExecution, StoredProcedureExecution, TaskExecution


class ParameterCollection:
    def __init__(self):
        self.parameters = dict()

    def normalize_name(self, name):
        return name.lower().replace("_", "").replace("@", "").replace("$", "")

    def __setitem__(self, name: str, value: Any) -> None:
        self.parameters[self.normalize_name(name)] = value

    def __getitem__(self, name: str) -> Any:
        normalized_name = self.normalize_name(name)
        if normalized_name in self.parameters:
            return self.parameters[normalized_name]
        else:
            raise KeyError(name)

    def update(self, input_dict : Dict) -> None:
        for key, value in input_dict.items():
            self[key] = value
            
    def get(self, name: str, default_value: Any=None) -> Any:
        normalized_name = self.normalize_name(name)
        if normalized_name in self.parameters:
            return self.parameters[normalized_name]
        else:
            return default_value


class JobExecution:
    """
    Context manager for logging job executions.
    """
    def __init__(self, job_name, backend=None, config="job.yml", **global_parameters):
        self.backend = backend
        self.environment_name = socket.gethostname()
        self.job_name = job_name

        self.id = None
        self.status = "Started"
        self.error_message = ""
        
        self.global_parameters = dict()
        if config:
            import yaml
            with open(config, 'rb') as doc:
                self.configure(yaml.safe_load(doc))            

        if not self.backend:
            self.backend = LoggingBackend()

        self.global_parameters.update(global_parameters)
        self.global_parameters["job_name"] = self.job_name

    def configure(self, config):
        if "environment" in config:
            self.environment_name = config["environment"]

        if "path" in config:
            for path in config["path"]:
                os.environ["PATH"] += path

        if "backend" in config:
            if "connection string" in config["backend"]:
                from .backends import DatabaseBackend
                import pyodbc
                connection = pyodbc.connect(config["backend"]["connection string"], autocommit=True)
                self.backend = DatabaseBackend(connection)

        if "parameters" in config:
            for key, value in config["parameters"].items():
                self[key] = value


    def __enter__(self):
        self.backend.before_job_execution(self)
        self.global_parameters["job_execution_id"] = self.id
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_value:
            self.status = "Failed"
            self.error_message = str(exc_value) + "\r\n" + "\r\n".join(traceback.format_tb(exc_tb))
            self.backend.after_job_execution(self)
        else:
            self.status = "Completed"
            self.backend.after_job_execution(self) 
        self.backend.close()

    def __setitem__(self, key, value):
        self.global_parameters[key] = value

    def __getitem__(self, key):
        return self.global_parameters[key]

    def process_task_execution(self, task_execution : TaskExecution, local_parameters : Dict = {}):
        "Process an arbitrary task execution in the context of the job"
        self.bind(task_execution, local_parameters)
        self.backend.before_task_execution(self, task_execution)
        try:
            task_execution.execute()
        except Exception as e:
            task_execution.error_message = str(e)
            task_execution.status = "Failed"
            self.backend.after_task_execution(self, task_execution)
            raise
        task_execution.status = "Completed"
        self.backend.after_task_execution(self, task_execution)
        return self
        
    def bind(self, task_execution : TaskExecution, local_parameters : Dict):
        "Collect all parameter values and bind the parameters of the task"
        parameters = ParameterCollection()
        parameters.update(self.global_parameters)
        parameters.update(local_parameters)
        parameters["job_execution_id"] = self.id
        parameters["task_execution_id"] = task_execution.id

        task_execution.bind_parameters(parameters)

    def execute(self, function, **local_parameters):
        "Execute a function in the context of the job"
        self.process_task_execution(FunctionExecution(function), local_parameters)

    def execute_procedure(self, connection, schema_name, *procedure_names, **local_parameters):
        "Execute a stored procedure in the context of the job"
        for procedure_name in procedure_names:
            self.process_task_execution(StoredProcedureExecution(connection, schema_name, procedure_name), local_parameters)

    def execute_r(self, *script_names, **local_parameters):
        "Execute an R script in the context of the job"
        for script_name in script_names:
            self.process_task_execution(RExecution(script_name), local_parameters)

    def execute_powershell(self, *script_names, **local_parameters):
        "Execute a powershell script in the context of the job"
        for script_name in script_names:
            self.process_task_execution(PowershellExecution(script_name), local_parameters)

