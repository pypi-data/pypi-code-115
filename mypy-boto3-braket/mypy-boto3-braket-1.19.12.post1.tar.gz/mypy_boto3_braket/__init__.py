"""
Main interface for braket service.

Usage::

    ```python
    from boto3.session import Session
    from mypy_boto3_braket import (
        BraketClient,
        Client,
        SearchDevicesPaginator,
        SearchQuantumTasksPaginator,
    )

    session = Session()
    client: BraketClient = session.client("braket")

    search_devices_paginator: SearchDevicesPaginator = client.get_paginator("search_devices")
    search_quantum_tasks_paginator: SearchQuantumTasksPaginator = client.get_paginator("search_quantum_tasks")
    ```
"""
from .client import BraketClient
from .paginator import SearchDevicesPaginator, SearchQuantumTasksPaginator

Client = BraketClient


__all__ = ("BraketClient", "Client", "SearchDevicesPaginator", "SearchQuantumTasksPaginator")
