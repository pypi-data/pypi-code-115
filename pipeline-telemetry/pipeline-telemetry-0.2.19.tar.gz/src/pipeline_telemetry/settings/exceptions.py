"""
Module to define customer excpetions for data_validator module

exceptions
- FieldNameMandatory
- UnknownInstruction
- InstructionRegisteredTwice
- RuleCanHaveOnlyOneInstruction
- BaseCountForSubProcessNotAdded
- TelemetryObjectAlreadyClosed
- StorageClassOfIncorrectType
- ProcessTypeMustBeOfClassProcessType
- ProcessTypeNotRegistered
"""
from typing import List


class FieldNameMandatory(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, instruction):
        message = f"For `{instruction}` instruction"
        super().__init__(message)


class MustHaveKeyMandatory(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, instruction):
        message = f"For `{instruction}` instruction"
        super().__init__(message)


class ExpectedCountMustBePositiveInt(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self):
        message = "".join(
            [
                "Ruleset does not contain `expected_count` or ",
                "expected count is negative",
            ]
        )
        super().__init__(message)


class UnknownInstruction(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, instruction):
        super().__init__(f"{instruction} not registered")


class InstructionRegisteredTwice(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, instruction_class):
        message = "".join(
            [
                f"{instruction_class.instruction} from class ",
                f"{instruction_class.__name__}.",
            ]
        )
        super().__init__(message)


class RuleCanHaveOnlyOneInstruction(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, rule):
        message = "".join(
            ["Rule contains multiple keys / instruction : ", ", ".join(rule.keys())]
        )
        super().__init__(message)


class InvalidSubProcess(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, sub_process: str, process_type):
        message = "".join(
            [
                f"Sub Process `{sub_process}` does not exist for ",
                f"process type `{process_type.name}`",
            ]
        )
        super().__init__(message)


class BaseCountForSubProcessNotAdded(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, sub_process):
        message = "".join(
            [
                f"Sub process {sub_process} has not yet been initialized.",
                f" First call increase_sub_process_base_count({sub_process}) ",
                "on telemetry instance",
            ]
        )
        super().__init__(message)


class TelemetryObjectAlreadyClosed(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self):
        message = "Telemetry object is already closed"
        super().__init__(message)


class StorageClassOfIncorrectType(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, class_name):
        message = "".join(
            [
                f"StorageClass `{class_name}` not a child ",
                "class of AbstractTelemetryStorage",
            ]
        )
        super().__init__(message)


class ProcessTypeMustBeOfClassProcessType(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self):
        message = "provide process_type not of class ProcessType"
        super().__init__(message)


class ProcessTypeNotRegistered(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self, process_type):
        message = f"provided process_type {process_type.name} not registered"
        super().__init__(message)


class ProcessTypesMustBeOfClassBaseEnumertor(Exception):
    """custom exception for Telemetry Module"""

    def __init__(self):
        message = "provided process_types enumerator not of class BaseEnumrator"
        super().__init__(message)


class InvalidSubProcessForProcessType(Exception):
    def __init__(self):
        message = "Provided sub process is not defined in ProcessType."
        super().__init__(message)


class InvalidTelemetryType(Exception):
    def __init__(self, available_types: List[str]):
        message = \
            f"Telemetry Type must be of type: {', '.join(available_types)}."
        super().__init__(message)


class ClassTelemetryParamsNotDefined(Exception):
    def __init__(self, object):
        class_name = object.__class__.__name__
        message = \
            f"Telemetry params not defined for class {class_name}"
        super().__init__(message)
