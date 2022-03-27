from moto.core.exceptions import JsonRESTError


class InvalidParameterValueException(JsonRESTError):
    def __init__(self, message):
        super().__init__("InvalidParameterValueException", message)


class ClusterNotFoundFault(JsonRESTError):
    def __init__(self, name=None):
        # DescribeClusters and DeleteCluster use a different message for the same error
        msg = f"Cluster {name} not found." if name else f"Cluster not found."
        super().__init__("ClusterNotFoundFault", msg)
